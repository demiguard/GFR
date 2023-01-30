import logging
import os
import django

# Init Django, note this is needed before you import django such as models.
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clairvoyance.settings')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'clairvoyance.settings'
    django.setup()


from datetime import date
from pathlib import Path
from pydicom import Dataset

import random
import shutil
import time

from main_page.libs import cache
from main_page.libs import dicomlib
from main_page.libs import server_config
from main_page.libs import ae_controller
from main_page.libs import dataset_creator
from main_page.models import ServerConfiguration, Department, HandledExaminations, Hospital
from main_page.libs.dirmanager import try_mkdir
from main_page import log_util
from main_page.libs.status_codes import DATASET_AVAILABLE, TRANSFER_COMPLETE

from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind, StudyRootQueryRetrieveInformationModelMove

# Create a logger just for the ris_thread
logger = log_util.get_logger(
  __name__,
  log_filename="ris_thread.log",
  log_level=logging.INFO
)

get_history = True

class RisFetcher():
  def __init__(self) -> None:
    self.date_last_iteration = date.today().day - 1
    self.get_history = get_history
    self.delay_min = server_config.SLEEP_DELAY_MIN
    self.delay_max = server_config.SLEEP_DELAY_MAX


  def delete_old_handled_studies(self):
    """
    Goes through the database and deletes old handled studies.

    This is just because we technically don't need to keep all that information.
    """
    today = date.today()
    for instance in HandledExaminations.objects.all():
      time_difference = today - instance.handle_day
      if time_difference.days > 14:
        instance.delete()

  def delete_old_images(self):
    """
      Deletes images in the folder
    """
    for hospital in Hospital.objects.all():
      hosp_image_dir = Path(
        server_config.IMG_RESPONS_DIR,
        hospital.short_name
      )
      if hosp_image_dir.exists():
        for image in hosp_image_dir.glob('*'):
          os.remove(image)
      else:
        hosp_image_dir.mkdir()

  def validate_department(self, department : Department):
    """This function validates a department regarding it having the
    nessesary information to perform a find query with history

    Args:
        department (Department): The Department to be validated

    Returns:
        Bool: If the department is valid
    """
    correctly_configured = True
    if department.hospital == None:
      logger.info(f"{department} doesn't have a configured A Hospital")
      correctly_configured = False
    if department.config == None:
      logger.info(f"{department} doesn't have a configuration")
      correctly_configured = False
    else:
      if department.config.ris == None:
        logger.info(f"{department} doesn't have a configured RIS address")
        correctly_configured = False
      if department.config.pacs == None:
        logger.info(f"{department} doesn't have a configured PACS address")
        correctly_configured = False
      if department.config.ris_calling == None:
        logger.info(f"{department} doesn't have a configured an AE title for RIS")
        correctly_configured = False
    return correctly_configured

  def validate_dataset(self, dataset : Dataset) -> bool:
    """Checks if a dataset have all the nessesary keys

    Args:
        dataset (Dataset): dataset to be validated

    Returns:
        Bool: Validity of dataset
    """
    valid_dataset = True
    if 'AccessionNumber' not in dataset:
      valid_dataset = False
    if 'PatientID' not in dataset:
      valid_dataset = False
    return valid_dataset

  def associate(self, department: Department):
    """Creates the associations nessesary for sending a find query

    Args:
        department (Department): _description_

    Returns:
        bool : If the connection were successful or not
    """
    self.ris_assoc = ae_controller.establish_assoc(
      ae_controller.create_find_AE(department.config.ris_calling),
      department.config.ris.ip,
      department.config.ris.port,
      department.config.ris.ae_title,
      logger
    )

    self.pacs_find_assoc = ae_controller.establish_assoc(
      ae_controller.create_find_AE(department.config.ris_calling),
      department.config.pacs.ip,
      department.config.pacs.port,
      department.config.pacs.ae_title,
      logger
    )
    self.pacs_move_assoc = ae_controller.establish_assoc(
      ae_controller.create_move_AE(department.config.ris_calling),
      department.config.pacs.ip,
      department.config.pacs.port,
      department.config.pacs.ae_title,
      logger
    )
    # Validate connections
    fully_connected = True
    if self.ris_assoc == None or not self.ris_assoc.is_established:
      fully_connected = False
    if self.pacs_find_assoc == None or not self.pacs_find_assoc.is_established:
      fully_connected = False
    if self.pacs_move_assoc == None or not self.pacs_move_assoc.is_established:
      fully_connected = False
    if not fully_connected:
      if self.ris_assoc != None and self.ris_assoc.is_established: # If this connected release the connection
        self.ris_assoc.release()
      if self.pacs_find_assoc != None and self.pacs_find_assoc.is_established:
        self.pacs_find_assoc.release()
      if self.pacs_move_assoc != None and self.pacs_move_assoc.is_established:
        self.pacs_move_assoc.release()

    return fully_connected

  def move_dataset(self, historic_dataset : Dataset, dataset_dir : Path):
    target_file = Path(f"{server_config.SEARCH_DIR}{historic_dataset.AccessionNumber}.dcm")
    destination = dataset_dir / f"{historic_dataset.AccessionNumber}.dcm"

    if target_file.exists():
      shutil.move(target_file, destination)
    else:
      logger.error(f"Historic dataset not found for Accession Number: {historic_dataset.AccessionNumber}")

  def get_historic_dataset(self, historic_dataset : Dataset, dataset_dir : Path):
    response = self.pacs_move_assoc.send_c_move(historic_dataset, self.sc.AE_title, StudyRootQueryRetrieveInformationModelMove)
    for status, identifier in response:
      if 'Status' in status:
        if status.Status == DATASET_AVAILABLE:
          pass
        elif status.Status == TRANSFER_COMPLETE:
          self.move_dataset(historic_dataset, dataset_dir)
        else:
          logger.info(f"Failed to transfer dataset, with status: {hex(status.Status)}")
      else:
        logger.error(f'Dataset does not have status attribute\n Status:\n{status}')


  def fetch_history(self, dataset: Dataset, dataset_dir : Path) -> None:
    history_queryDataset = dataset_creator.create_search_dataset('',dataset.PatientID, '','','')
    response = self.pacs_find_assoc.send_c_find(history_queryDataset, StudyRootQueryRetrieveInformationModelFind)
    logger.debug("Fetching history")
    for status, historic_dataset in response:
      if 'Status' in status:
        if status.Status == DATASET_AVAILABLE:
          self.get_historic_dataset(historic_dataset, dataset_dir)
        elif status.Status == TRANSFER_COMPLETE:
          pass
        else:
          logger.error(f"Failed to transfer dataset with message: {status}")
      else:
        logger.error(f"Failed finding historic dataset with Accession Number: {dataset.AccessionNumber}")


  def handle_ris_dataset(self, dataset : Dataset, department : Department) -> None:
    if not self.validate_dataset(dataset):
      logger.error(f"Invalid Dataset:{dataset}")
      return

    dataset_dir = Path(f"{server_config.FIND_RESPONS_DIR}{department.hospital.short_name}/{dataset.AccessionNumber}/")
    delete_dir = Path(f"{server_config.DELETED_STUDIES_DIR}{department.hospital.short_name}/{dataset.AccessionNumber}/")

    if dataset.AccessionNumber in self.handled_examinations or dataset_dir.exists() or delete_dir.exists():
      logger.debug(f"Handled examinations: {self.handled_examinations}")
      logger.debug(f"Path: {dataset_dir} - exists: {dataset_dir.exists()}")
      logger.debug(f"Path: {delete_dir} - exists: {delete_dir.exists()}")
      return

    dataset_dir.mkdir(parents=True, exist_ok=True)
    file_path = f"{dataset_dir}/{dataset.AccessionNumber}.dcm"
    try:
      dicomlib.save_dicom(file_path, dataset)
    except ValueError as e:
      logger.error(f"Failed to save dicom file at {file_path}, got exception {e}")
      shutil.rmtree(dataset_dir)
      return

    if self.get_history: # Fetches the history of datasets
      self.fetch_history(dataset, dataset_dir)
    else:
      logger.info("Skipping fetching history")

  def run(self) -> None:
    date_last_iteration = date.today().day - 1
    while True:
      logger.info("Starting RIS Fetcher service")
      # Get Data from database to do a fetch from ris
      self.sc = ServerConfiguration.objects.get(pk=1)
      self.handled_examinations = { he.accession_number : he.handle_day
        for he in HandledExaminations.objects.all() }

      for department in Department.objects.all():
        # Validate Config
        if not self.validate_department(department): # Logging happens inside of Validate Department
          continue

        # Create associations
        if not self.associate(department): # This function set self.ris_assoc, self.pacs_find_assoc, self.pacs_move_assoc
          continue
        # Do the pull request
        query_dataset = dataset_creator.generate_ris_query_dataset(department.config.ris_calling)

        response = self.ris_assoc.send_c_find(query_dataset, StudyRootQueryRetrieveInformationModelFind)
        for status, dataset in response:
          if 'Status' in status:
            if status.Status == DATASET_AVAILABLE:
              self.handle_ris_dataset(dataset, department)
            elif status.Status == TRANSFER_COMPLETE:
              logger.debug(f"Handled respose to {department}")
              pass # The Transfer is compelete and the association can not be closed.
            else:
              logger.info(f"Failed to Transfer dataset with message {status}")

        # Free connections
        self.ris_assoc.release()
        self.pacs_find_assoc.release()
        self.pacs_move_assoc.release()
      #End of Department for loop

      today = date.today().day #mabye just save the entire object
      if today != date_last_iteration:
        #logger.info('Cleaning Cache and Image directory')
        cache.clean_cache(14)
        self.delete_old_images()
        self.delete_old_handled_studies()
      date_last_iteration = today

      # Sleep the thread
      delay = random.uniform(self.delay_min, self.delay_max) * 60
      logger.info(f'Ris thread going to sleep for {delay:.2f} sec.')
      time.sleep(delay)
    #End of Infinite While loop

if __name__ == "__main__":
  # Recreate Handled examinations
  risFetcher = RisFetcher()
  risFetcher.run()

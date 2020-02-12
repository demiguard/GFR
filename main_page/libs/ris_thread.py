import pydicom
import pynetdicom
import logging
import os
import time
import datetime
import random
import glob
import shutil
from pathlib import Path
from threading import Thread
import re

from typing import Type

from main_page.libs import dicomlib
from main_page.libs import server_config
from main_page.libs import ae_controller
from main_page.libs import dataset_creator
from main_page import models
from main_page.libs.dirmanager import try_mkdir
from main_page import log_util

# Create a logger just for the ris_thread
logger = log_util.get_logger(
  __name__, 
  log_filename="ris_thread.log", 
  log_level=server_config.THREAD_LOG_LEVEL
)


class RisFetcherThread(Thread):
  """
  Thread subclass for peridically retreiving studies from RIS 
  to be shown on list_studies.

  Once a study has been received it's prior history for GFR studies is 
  retreieved aswell, since it takes a long time to fetch the previous history
  for the patient, we do it here such that the history is ready once a new
  study is to be computed. (we refer to this a "worklist-prefetching")

  This class is meant to be used as a singleton class
  """

  __instance = None
  @staticmethod
  def get_instance(server_ae, delay_min, delay_max):
    """
    Retreives or instantiates the thread (this is a singleton class)

    Args:
  
    """
    if RisFetcherThread.__instance == None:
      RisFetcherThread(server_ae, delay_min, delay_max)
    return RisFetcherThread.__instance

  def __init__(self, server_ae: str, delay_min, delay_max):
    """
    Initializes the thread instance

    Args:
      server_ae: server AET (SCP server AET)
      delay_min: min. number of minutes to sleep for
      delay_max: max. number of minutes to sleep for
    """
    logger.info("Starting initialization of thread")

    # Ensure singleton pattern
    if RisFetcherThread.__instance != None:
      raise Exception("This is a singleton...")
    else:
      RisFetcherThread.__instance = self

    # Set instance variables
    self.running = False
    self.server_ae = server_ae
    self.today = datetime.datetime.now().day
    self.delay_min = delay_min
    self.delay_max = delay_max

    # This is a daemon, i.e. background worker thread
    Thread.__init__(
      self,
      name='RisFetcherThread',
      daemon=True,
      group=None
    )

    logger.info("Initialization done")

  def handle_c_move(self, dataset, *args, **kwargs):
    """
      This is the handler from pacs response C-MOVE
      REMEMBER a C-MOVE doesn't return the file, but instead a status update when the reciever have recieved the file
      In this case the reciever is the SCP server which just stores it under server_config.SEARCH_DIR
    """
    accession_number = kwargs['accession_number']
    dataset_dir      = kwargs['dataset_dir']
    logger           = kwargs['logger']

    target_file = f"{server_config.SEARCH_DIR}{accession_number}.dcm"
    destination = f"{dataset_dir}{accession_number}.dcm"

    if not os.path.exists(destination):
      shutil.move(target_file, destination)
    else:
      logger.critical(f"Got duplicate move response from PACS with accession number: {accession_number}")

  def get_historic_examination(self, dataset, *args, **kwargs): 
    """
    Handler for C-FIND query from PACS to get the historic data
    """
    department       = kwargs['department']
    dataset_dir      = kwargs['dataset_dir'] 
    logger           = kwargs['logger']
    accession_number = dataset.AccessionNumber
    
    pacs_move_association = kwargs['pacs_move_association']

    ae_controller.send_move(
      pacs_move_association,
      department.config.pacs_calling,
      dataset,
      self.handle_c_move,
      accession_number=accession_number,
      dataset_dir=dataset_dir,
      logger=logger
    )

  def save_resp_to_file(self, dataset, **kwargs):
    """
    Processing function for saving successful response to files

    Args:
      dataset: response dataset

    Kwargs:
      logger: logger to use
      hospital_shortname: current hospital shortname e.g. RH

    Throws:
      Keyerror: When not called with correct parameters  
    """
    department = kwargs['department']
    pacs_find_association = kwargs['pacs_find_association']
    pacs_move_association = kwargs['pacs_move_association']
    logger = kwargs['logger']

    hospital_shortname = department.hospital.short_name

    active_studies_dir  = server_config.FIND_RESPONS_DIR
    deleted_studies_dir = server_config.DELETED_STUDIES_DIR

    try:
      dataset_dir = f"{active_studies_dir}{hospital_shortname}/{dataset.AccessionNumber}/"
      deleted_dir = f"{deleted_studies_dir}{hospital_shortname}/{dataset.AccessionNumber}/"

      file_exists = (os.path.exists(dataset_dir) or os.path.exists(deleted_dir))
      file_handled = models.HandledExaminations.objects.filter(accession_number=dataset.AccessionNumber).exists()

      # Check if not in active_dicom_objects or deleted_studies and not in handled_examinations
      if not file_exists and not file_handled:
        try_mkdir(dataset_dir, mk_parents=True)

        dicomlib.save_dicom(f"{dataset_dir}{dataset.AccessionNumber}.dcm", dataset)

        # Now retrieve the previous history
        history_query_set = dataset_creator.create_search_dataset(
          '',
          dataset.PatientID,
          '',
          '',
          ''
        )

        # Send the C-FIND to pacs
        ae_controller.send_find(
          pacs_find_association,
          history_query_set,
          self.get_historic_examination,
          dataset_dir=dataset_dir,
          department=department,
          pacs_move_association=pacs_move_association,
          logger=logger
        )

        logger.info(f"Successfully save dataset: {dataset_dir}")
      else:
        logger.info(f"Skipping file: {dataset_dir}, as it already exists or has been handled")
    except AttributeError as e:
      logger.error(f"failed to load/save dataset, with error: {e}")

  def try_delete_old_images(self, hospitals):
    """
    Delete old generated images if more than a day has passed
    """
    today = datetime.datetime.now().day
    if today != self.today:
      # Delete Temperary files
      logger.info("Date changed, Removing Image Files")
      self.today = today

      for hospital in hospitals:
        hosp_image_dir = Path(
          server_config.IMG_RESPONS_DIR,
          hospital
        )

        if hosp_image_dir.is_dir():
          shutil.rmtree(hosp_image_dir)
          logging.info(f"Deleting image directory: {hosp_image_dir}")

  def run(self):
    """
    Routine function to periodically run
    """
    self.running = True
  
    logger.info("Starting run routine")
    
    while self.running:
      logger.info("RIS thread sending response")

      # For each hospital, we want to query to see if there's any new studies
      # for each study we want to retrieve the patient history from pacs,
      # this process requires a combination of C-FIND and C-MOVE queries
      hospitals = {hospital.short_name for hospital in models.Hospital.objects.all() if hospital.short_name}

      for department in models.Department.objects.all():
        # Send C-FIND requests to RIS
        # All associations are established here, since moving them into each
        # processing function would mean that a new connection is opened and
        # closed after each dataset has been processed, thus putting
        # unnecessary stress on PACS
        try:
          ris_association = ae_controller.connect(
            department.config.ris_ip,
            department.config.ris_port,
            department.config.ris_calling,
            department.config.ris_aet,
            ae_controller.FINDStudyRootQueryRetrieveInformationModel,
            logger = logger
          )
          pacs_find_association = ae_controller.connect(
            department.config.pacs_ip,
            department.config.pacs_port,
            department.config.pacs_calling, #TODO Change this back to config.pacs_calling when AE_titles is set up correctly
            department.config.pacs_aet,
            ae_controller.FINDStudyRootQueryRetrieveInformationModel,
            logger = logger
          )

          pacs_move_association = ae_controller.connect(
            department.config.pacs_ip,
            department.config.pacs_port,
            department.config.pacs_calling,
            department.config.pacs_aet,
            ae_controller.MOVEStudyRootQueryRetrieveInformationModel,
            logger = logger
          )
        except Exception as Error:
          logger.error(f"Could not connect for department config : {department.config.id}")

          #Unsure if I need the outer if-statement, but it's need if you just run it in the interpredritor
          if 'ris_association' in dir(): 
            if ris_association:
              ris_association.release()
          if 'pacs_find_association' in dir():
            if pacs_find_association:
              pacs_find_association.release()
          if 'pacs_move_association' in dir():
            if pacs_move_association:
              pacs_move_association.release()

          continue

        if not (ris_association and pacs_find_association and pacs_move_association):
          logger.info(f"Skipping config: {department.config.id}")

          if ris_association:
            ris_association.release()
          if pacs_find_association:
            pacs_find_association.release()
          if pacs_move_association:
            pacs_move_association.release()

          continue


        query_dataset = dataset_creator.generate_ris_query_dataset(department.config.ris_calling)        

        ae_controller.send_find(
          ris_association, 
          query_dataset, 
          self.save_resp_to_file,
          logger=logger,
          department=department,
          pacs_find_association=pacs_find_association,
          pacs_move_association=pacs_move_association
        )

        ris_association.release()
        pacs_find_association.release()
        pacs_move_association.release()
      
      # End of department for-loop

      self.try_delete_old_images(hospitals)
      
      # Sleep the thread
      delay = random.uniform(self.delay_min, self.delay_max) * 60
      logger.info(f'Ris thread going to sleep for {delay} sec.')
      
      time.sleep(delay)

    logger.info("Terminated ris_thread run loop")

  def apply_kill_to_self(self):
    """
    Termiantes the periodic loop. Intended for restarting the thread
    """
    self.running = False
    logger.info("Killing self")

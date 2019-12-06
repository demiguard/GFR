import pydicom
import pynetdicom
import logging
import os
import time
import datetime
import random
import glob
import shutil
from . import dicomlib
from . import dataset_creator
from . import server_config 
from . import ris_thread_config_gen
from . import ae_controller

from main_page import models
from .dirmanager import try_mkdir
from threading import Thread
from typing import Type

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

def setup_logger(name, log_file, level=logging.INFO):
  """
  Generates loggers

  Args:
    name: name of the logger 
          (a logger can be retreived by calling logging.getLogger(<LOGGER_NAME>))
    log_file: filepath to placement of the logfile on the system
  
  Kwargs:
    level: which level should the logger log on (default=INFO)
  """
  handler = logging.FileHandler(log_file)        
  handler.setFormatter(formatter)

  logger = logging.getLogger(name)
  logger.setLevel(level)
  logger.addHandler(handler)

  return logger

# Get the ris threads logger
logger = setup_logger(
  "ris-thread-log", 
  f"{server_config.LOG_DIR}ris_thread.log", 
  level=server_config.THREAD_LOG_LEVEL
)


class RisFetcherThread(Thread):
  """
  Thread subclass for retreiving studies periodically, as to avoid problems with
  study information first being entered the day after the study was actually made
  """

  def __init__(self, config, server_ae):
    """
    Initializes a fetcher thread instance

    Args:
      config: dictionary containing setup parameters for the thread to query RIS
    """
    logger.info("starting initialization of thread")

    # Ensure singleton pattern
    if RisFetcherThread.__instance != None:
      raise Exception("This is a singleton...")
    else:
      RisFetcherThread.__instance = self

    self.config = config
    self.running = False
    self.server_ae = server_ae
    self.today = datetime.datetime.now().day

    # Thread is a daemon, i.e. background worker thread
    Thread.__init__(
      self,
      name='RisFetcherThread',
      daemon=True,
      group=None
    )

    logger.info("initialization done")

  def handle_c_move(dataset, *args, **kwargs):
    """
      This is the handler from pacs response C-move
      REMEMBER a C-find doesn't return the file, but instead a status update when the reciever have recieved the file
      In this case the reciever is this server
    """
    accession_number = kwargs['accession_number']
    dataset_dir      = kwargs['dataset_dir']

    target_file = f"{server_config.SEARCH_DIR}{accession_number}.dcm"
    destination = f"{dataset_dir}{accession_number}.dcm"

    shutil.move(target_file, destination)

  def get_historic_examination(dataset, *args, **kwargs): 
    """
      This is handler for handling the C-find response from Pacs

      NOTE: To designers, you might end up fucked since, if there's more than one response to the same study.
      Now you may think, why would i get two studies for a unique identifier, however my sweet sweet summer child, world is cruel like that

    """
    move_association = kwargs['move_association']
    department       = kwargs['department']
    dataset_dir      = kwargs['dataset_dir'] 
    accession_number = dataset.AccessionNumber

    ae_controller.send_move(
      move_association,
      department.config.pacs_calling,
      dataset,
      self.handle_c_move,
      accession_number=accession_number,
      dataset_dir=dataset_dir
    )

  def save_resp_to_file(dataset, **kwargs) -> None:
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

    department        = kwargs['department'])
    find_association  = kwargs['find_association']

    hospital_shortname = department.hospital.short_name

    active_studies_dir  = server_config.FIND_RESPONS_DIR
    deleted_studies_dir = server_config.DELETED_STUDIES_DIR

    try:
      dataset_dir = f"{active_studies_dir}{hospital_shortname}/{dataset.AccessionNumber}/"  # Check if in active_dicom_objects
      deleted_dir = f"{deleted_studies_dir}{hospital_shortname}/{dataset.AccessionNumber}/" # Check if in deleted_studies

      file_exists = (os.path.exists(dataset_dir) or os.path.exists(deleted_dir))
      file_handled = models.HandledExaminations.objects.filter(accession_number=dataset.AccessionNumber).exists()

      if not file_exists and not file_handled:
        try_mkdir(dataset_dir, mk_parents=True)

        dicomlib.save_dicom(f"{dataset_dir}{dataset.AccessionNumber}.dcm", dataset)

        #Here We need to retrieve History
        move_association = ae_controller.connect(
          department.configpacs_ip,
          int(department.config.pacs_port),
          department.config.pacs_calling,
          department.config.pacs_aet,
          MOVEStudyRootQueryRetrieveInformationModel
        )

        #Create the query dataset
        history_query_set = dataset_creator.create_search_dataset(
          '',
          dataset.PatientID,
          '',
          ''
        )
        #Send the C-find to pacs
        ae_controller.send_find(
          find_association,
          history_query_set,
          self.get_historic_examination,
          dataset_dir=dataset_dir,
          department=department,
          move_association=move_association
        )

        move_association.release()

        logger.info(f"Successfully save dataset: {dataset_dir}")
     else:
        logger.info(f"Skipping file: {dataset_dir}, as it already exists or has been handled")
   except AttributeError as e:
      logger.error(f"failed to load/save dataset, with error: {e}")



  def run(self):
    """
    Routine function to periodically run
    """
    self.running = True
  
    logger.info("Starting run routine")
    
    while self.running:
      logger.info("RIS thread sending response")
      hospitals = [] #This is filled later

      # A bit of Documentation:
      # So for each department, we want to query to see if there's any new studies
      # For each Study we want to Retrieve the patient history from pacs,
      # This process requires a C-find and a C-Move
      for department in models.Department.objects.all():
        if department.hospital.short_name:
          hospitals.append(department.hospital.short_name) #This is used later for image deletion

        # Send C-FIND requests to RIS
        ris_association = ae_controller.connect(
          department.config.ris_ip,
          department.config.ris_port,
          department.config.ris_calling,
          department.config.ris_AET,
          ae_controller.FINDStudyRootQueryRetrieveInformationModel
        )

        pacs_association = ae_controller.connect(
          department.config.pacs_ip,
          department.config.pacs_port,
          department.config.pacs_calling,
          department.config.pacs_AET,
          ae_controller.FINDStudyRootQueryRetrieveInformationModel
        )

        query_dataset = dataset_creator.generate_ris_query_dataset(department.config.ris_calling)        

        ae_controller.send_find(
          ris_association, 
          query_dataset, 
          self.save_resp_to_file,
          logger=logger,
          department=department,
          find_association=pacs_association
        )

        ris_association.release()
        pacs_association.release()
      #End Department for loop

      # Sleep the thread
      delay = random.uniform(delay_min, delay_max) * 60
      logger.info(f'Ris thread going to sleep for {delay} sec.')

      # Re-read config for possible updates

      today = datetime.datetime.now().day
      if today != self.today:
        #Delete Temperary files
        logger.info("Date changed, Removing Image Files")
        self.today = today

        image_folder = server_config.IMG_RESPONS_DIR
        for hospital in hospitals:
          files = glob.glob(f'{image_folder}{hospital}/*')
          for f in files:
            if os.path.exists(f):
              if not os.path.isdir(f):
                logging.info(f"Deleting image at {f}")
                os.remove(f)


      time.sleep(delay)
      #End while Loop

    logger.info("Terminated run loop")

  def apply_kill_to_self(self):
    """
    Termiantes the periodic loop. Intended for restarting the thread
    """
    self.running = False
    logger.info("Killing self")

  __instance = None
  @staticmethod
  def get_instance(config):
    """
    Retreives or instantiates the thread (this is a singleton class)

    Args:
      config: initial configuration for the thread to use
    """
    if RisFetcherThread.__instance == None:
      RisFetcherThread(config)
    return RisFetcherThread.__instance

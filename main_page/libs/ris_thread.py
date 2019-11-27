import pydicom
import pynetdicom
import logging
import os
import time
import datetime
import random
import glob
from . import dicomlib
from . import dataset_creator
from . import server_config 
from . import ris_thread_config_gen
from . import ae_controller

from main_page import models
from .dirmanager import try_mkdir
from threading import Thread

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
  

  def run(self):
    """
    Routine function to periodically run
    """
    self.running = True
  
    logger.info("Starting run routine")
    
    while self.running:
      logger.info("RIS thread sending response")
      
      # Extract configuration parameters
      try:
        ris_ip = self.config['ris_ip']
        ris_port = int(self.config['ris_port'])
        ris_AET = self.config['ris_AET']
        delay_min = int(self.config['Delay_minimum'])
        delay_max = int(self.config['Delay_maximum'])
        AE_titles = self.config['AE_items']

        assert delay_min <= delay_max
      except KeyError as KE:
        raise AttributeError(
          f"""Unable to read from config, '{KE}'.
          self.config={self.config}"""
        )

      # Send C-FIND requests to RIS
      association = ae_controller.connect(
        ris_ip,
        ris_port,
        self.server_ae,
        ris_AET,
        ae_controller.FINDStudyRootQueryRetrieveInformationModel
      )

      for AET, hospital_shortname in AE_titles.items():
        query_dataset = dataset_creator.generate_ris_query_dataset(AET)        

        ae_controller.send_find(
          association, 
          query_dataset, 
          ae_controller.save_resp_to_file,
          logger=logger,
          hospital_shortname=hospital_shortname
        )

      # Sleep the thread
      delay = random.uniform(delay_min, delay_max) * 60
      logger.info(f'Ris thread going to sleep for {delay} sec.')

      # Re-read config for possible updates
      self.config = ris_thread_config_gen.read_config()

      today = datetime.datetime.now().day
      if today != self.today:
        #Delete Temperary files
        logger.info("Date changed, Removing Image Files")
        self.today = today

        hospitals = server_config.HOSPITALS.keys()
        image_folder = server_config.IMG_RESPONS_DIR
        for hospital in hospitals:
          files = glob.glob(f'{image_folder}{hospital}/')
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

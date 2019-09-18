import pydicom
import pynetdicom
import logging
import os
import time
import datetime
import random
from . import dicomlib
from . import dataset_creator
from . import server_config 
from . import ris_thread_config_gen

from .dirmanager import try_mkdir
from threading import Thread

"""
    NOTE TO self and furture devs
    Because this thread is started at run time, it cannot access the django database as such it must be manually configured using this file.
    This includes the files:
      dicomlib.py
      dataset_creator.py

    This file describes a thread that pings ris every given time interval, retrieving 
"""

logger = logging.getLogger()


class RisFetcherThread(Thread):
  """
  Thread subclass for retreiving studies periodically, as to avoid problems with
  study information first being entered the day after the study was actually made
  """
  
  def run(self):
    """
      Routine function to periodically run
    """
    self.running = True
    
    DICOM_FILE_RECIEVED = 0xFF00
  
    logger.info(f"{self.log_name}: Starting run routine")
    
    while self.running:
      logger.info(f"{self.log_name}: RIS thread sending response")
      try:
        ris_ip = self.config['ris_ip']
        ris_port = int(self.config['ris_port'])
        ris_AET = self.config['ris_AET']
        delay_min = int(self.config['Delay_minimum'])
        delay_max = int(self.config['Delay_maximum'])
        AE_titles = self.config['AE_items']

        assert delay_min <= delay_max
      except KeyError as KE:
        raise AttributeError(f'{KE} : {self.config}') # NOTE: Why change the exception class like this?

      ae = pynetdicom.AE(ae_title=server_config.SERVER_AE_TITLE)
      FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.1'
      ae.add_requested_context(FINDStudyRootQueryRetrieveInformationModel)

      association = ae.associate(
        ris_ip,
        ris_port,
        ae_title=ris_AET
      )

      if association.is_established:
        # Send C-FIND to fetch studies for each AET
        for AET, hospital_shortname in AE_titles.items():
          response = association.send_c_find(
            dataset_creator.generate_ris_query_dataset(AET),
            query_model='S'
          )

          for status, dataset in response:
            if status.Status == DICOM_FILE_RECIEVED:
              try:
                filepath = f'{server_config.FIND_RESPONS_DIR}{hospital_shortname}/{dataset.AccessionNumber}.dcm'
                dicomlib.save_dicom(filepath, dataset)
              except Exception as e: # Possible AttributeError, due to possible missing accession number
                logger.error(f"{self.log_name}: failed to load/save dataset, with error: {e}")  
            else:
              logger.info(f"{self.log_name}: Failed to transfer file, with status: {status.Status}")
              break

        association.release()
      else:
        logger.error(f"{self.log_name}: Unable to establish connection to RIS")

      # Association done
      delay = random.uniform(delay_min, delay_max) * 60
      logger.info(f'Ris thread going to sleep for {delay} min.')

      # Re-read config for possible updates
      self.config = ris_thread_config_gen.read_config()

      time.sleep(delay)

    logger.info(f"{self.log_name}: Terminated run loop")

  def apply_kill_to_self(self):
    """
    Termiantes the periodic loop. Intended for restarting the thread
    """
    self.running = False
    logger.info(f"{self.log_name}: killing self")

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

  def __init__(self, config):
    """
      Initializes a fetcher thread instance

      Args:
        config: dictionary containing required 
    """
    self.log_name = type(self).__name__
    logger.info(f"{self.log_name}: starting initialization of thread")

    # Ensure singleton pattern
    if RisFetcherThread.__instance != None:
      raise Exception("This is a singleton...")
    else:
      RisFetcherThread.__instance = self

    self.config = config
    self.running = False

    # Thread is a daemon, i.e. background worker thread
    Thread.__init__(
      self,
      name='RisFetcherThread',
      daemon=True,
      group=None
    )

    logger.info(f"{self.log_name}: initialization done")
  
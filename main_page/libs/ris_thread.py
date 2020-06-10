import pydicom
import pynetdicom
import logging
import django
import os
import time
import datetime
import random
import glob
import shutil
import multiprocessing
import threading
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
#This lib contains functions that should be moved an propriate directory
#Specificly ris_query_wrapper.get_studies
from main_page.libs.query_wrappers import ris_query_wrapper 

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
    self.ris_ae_finds = {} 
    self.pacs_ae_finds = {}
    self.pacs_ae_moves = {}
    self.departments = {}
    self.handled_examinations = {}
    self.cache_life_time = 14 #Days

    # This is a daemon, i.e. background worker thread
    Thread.__init__(
      self,
      name='RisFetcherThread',
      daemon=True,
      group=None
    )

    logger.info("Initialization done")

  def Update_date(self):
    """
      This function updates the today variable

      Remark:
        It's very important that this function is called after ALL daily cleaning functions

    """
    today = datetime.datetime.now().day
    if self.today != today:
      self.today = today


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
      department['pacs_calling'],
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
    django.db.connection.close()
    department = kwargs['department']
    pacs_find_association = kwargs['pacs_find_association']
    pacs_move_association = kwargs['pacs_move_association']
    logger = kwargs['logger']

    logger.info(department)

    hospital_shortname = department['hospital']

    active_studies_dir  = server_config.FIND_RESPONS_DIR
    deleted_studies_dir = server_config.DELETED_STUDIES_DIR

    dataset_dir = f"{active_studies_dir}{hospital_shortname}/{dataset.AccessionNumber}/"
    deleted_dir = f"{deleted_studies_dir}{hospital_shortname}/{dataset.AccessionNumber}/"

    file_exists = (os.path.exists(dataset_dir) or os.path.exists(deleted_dir))
    file_handled = dataset.AccessionNumber in self.handled_examinations

    # Check if not in active_dicom_objects or deleted_studies and not in handled_examinations
    if not file_exists and not file_handled:
      try_mkdir(dataset_dir, mk_parents=True) # This should be removed on failure, so we can try again

      file_path = f"{dataset_dir}{dataset.AccessionNumber}.dcm"
      try:
        dicomlib.save_dicom(file_path, dataset)
      except ValueError as e:
        logger.error(f"Failed to save received dicom file: {file_path}, got exception {e}")
        shutil.rmtree(dataset_dir) # Remove created dir. so file_handled is false in next try
        return

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
    
  def try_delete_old_images(self, hospitals):
    """
    Delete old generated images if more than a day has passed
    """
    today = datetime.datetime.now().day
    if today != self.today:
      # Delete Temperary files
      logger.info("Date changed, Removing Image Files")

      for hospital in hospitals:
        hosp_image_dir = Path(
          server_config.IMG_RESPONS_DIR,
          hospital
        )

        if hosp_image_dir.is_dir():
          shutil.rmtree(hosp_image_dir)
          logging.info(f"Deleting image directory: {hosp_image_dir}")

  def kill_connections(self, AE):
    """
      Murders all active connections for an AE. This may happen mid-connection, and I have not tested all the infinite edge cases.
    """
    for assoc in AE.active_associations:
      assoc.abort()

  def pull_request(self, ris_find_ae):
    """
    This function handles a single pull request for a single AE, It may be cancel by the ris_thread
    Note that this is a thread spawned by the thread. #INCEPTION

    CRITICAL: It is critical that this functions, and all function called by this function does not interact with the database
      - It's a SQLite db, which doesn't handle concurrency very well, therefore all information from the db must be pre-queried and saved in the object
        * Currently this information is:
          # connection parameters handled in Department and their respective configs
          # Handled examinations
      - function self.update_self handles this currently

    """
    django.db.connections.close_all()
    ae_title_b   = ris_find_ae.ae_title
    department   = self.departments[ae_title_b]
    pacs_ae_find = self.pacs_ae_finds[ae_title_b]
    pacs_ae_move = self.pacs_ae_moves[ae_title_b]

    #Establishing Connection
    ris_assoc = ae_controller.establish_assoc(
      ris_find_ae,
      department['ris_ip'],
      department['ris_port'],
      department['ris_aet'],
      logger
    )
    if ris_assoc == None:
      return #Error have been logged in the ae_controler

    pacs_find_assoc = ae_controller.establish_assoc(
      pacs_ae_find,
      department['pacs_ip'],
      department['pacs_port'],
      department['pacs_aet'],
      logger
    )
    if pacs_find_assoc == None:
      ris_assoc.release()
      return  

    pacs_move_assoc = ae_controller.establish_assoc(
      pacs_ae_move,
      department['pacs_ip'],
      department['pacs_port'],
      department['pacs_aet'],
      logger
    )
    if pacs_move_assoc == None:
      ris_assoc.release()
      pacs_find_assoc.release()
      return
    #Connections has been established

    query_dataset = dataset_creator.generate_ris_query_dataset(department['ris_calling'])        
    
    ae_controller.send_find(
          ris_assoc, 
          query_dataset, 
          self.save_resp_to_file,
          logger=logger,
          department=department,
          pacs_find_association=pacs_find_assoc,
          pacs_move_association=pacs_move_assoc
        )

    ris_assoc.release()
    pacs_find_assoc.release()
    pacs_move_assoc.release()
    return

  def update_self(self):
    ae_titles = []
    for department in models.Department.objects.all():
      department_config = department.config
      if department_config.ris_calling == None or department_config.ris_calling == '':
        continue
      ae_title = pynetdicom.utils.validate_ae_title(department_config.ris_calling)
      ae_titles.append(ae_title)
      
      department_dir = { 
        'ris_aet' :     department_config.ris_aet,
        'ris_ip'  :     department_config.ris_ip,
        'ris_port':     department_config.ris_port,
        'ris_calling':  department_config.ris_calling,
        'pacs_aet':     department_config.pacs_aet,
        'pacs_ip':      department_config.pacs_ip,
        'pacs_port':    department_config.pacs_port,
        'pacs_calling': department_config.pacs_calling,
        'hospital'    : department.hospital.short_name
      }

      if not(ae_title in self.ris_ae_finds):
        self.ris_ae_finds[ae_title] = ae_controller.create_find_AE(ae_title)

      if not(ae_title in self.pacs_ae_finds):
        self.pacs_ae_finds[ae_title] = ae_controller.create_find_AE(department_config.pacs_calling)

      if not(ae_title in self.pacs_ae_moves):
        self.pacs_ae_moves[ae_title] = ae_controller.create_move_AE(department_config.pacs_calling)
      
      self.departments[ae_title] = department_dir

      #1 is a dummy value, what is need is the look up functionality, such that its not a list pythons looks through, but a hash table
      self.handled_examinations = { handled_examination.accession_number : 1 for handled_examination in models.HandledExaminations.objects.all()}   
      #End for department for loop 
    #Clean up of unused ae_titles
    for key in self.ris_ae_finds.keys():
      if not(key in ae_titles):
        del self.ris_ae_finds[key]
    
    for key in self.pacs_ae_finds.keys():
      if not(key in ae_titles):
        del self.pacs_ae_finds[key]
    
    for key in self.pacs_ae_moves.keys():
      if not(key in ae_titles):
        del self.pacs_ae_moves[key]

    for key in self.departments.keys():
      if not(key in ae_titles):
        del self.departments[key]    

  def run(self):
    """
    Routine function to periodically run
    """
    self.running = True

    logger.info(django.db.connection.queries)

    logger.info("Starting run routine")
    
    while self.running:
      logger.info("RIS thread sending response")
      self.update_self()

      for ae_title in self.ris_ae_finds.keys():
        query_process = threading.Thread(target=self.pull_request, args=[self.ris_ae_finds[ae_title]])
        query_process.start()
        query_process.join(60) #60 is timeout move this to somewhere visable
        # After timeout reset connection
        if query_process.is_alive():
          logger.error(f'Timeout have happened for: {ae_title}!')
          self.kill_connections(self.ris_ae_finds[ae_title])
          self.kill_connections(self.pacs_ae_find[ae_title])
          self.kill_connections(self.pacs_ae_move[ae_title])
          query_process.terminate()
          query_process.join()
        else:
          logger.info(f'Finished Query for title: {ae_title}')

      hospitals = [hospital.short_name for hospital in models.Hospital.objects.all() if hospital.short_name]

      #Daily clean up
      today = datetime.datetime.now().day
      if today != self.today:
        cache.clean_cache(self.cache_life_time)
      self.try_delete_old_images(hospitals)
      self.Update_date() #This updates today
      
      # Sleep the thread
      delay = random.uniform(self.delay_min, self.delay_max) * 60
      logger.info(f'Ris thread going to sleep for {delay:.2f} sec.')
      
      time.sleep(delay)

    logger.info("Terminated ris_thread run loop")

  def apply_kill_to_self(self):
    """
    Termiantes the periodic loop. Intended for restarting the thread
    """
    self.running = False
    logger.info("Killing self")

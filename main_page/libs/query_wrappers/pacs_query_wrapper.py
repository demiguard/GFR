import pydicom, pynetdicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict
from pynetdicom import AE, StoragePresentationContexts, evt
import os
import logging
import sys
import shutil
import glob
import datetime
import calendar
import numpy
import pandas
import random
import csv
import threading
import time
import json

from main_page.libs import ae_controller
from main_page.libs.dirmanager import try_mkdir
from .. import dicomlib, dataset_creator
from .. import server_config
from ..clearance_math import clearance_math
from .. import formatting


from main_page import log_util

logger = log_util.get_logger(__name__)

def move_study_from_search_cache(dataset, *args, **kwargs):
  """
    This is the hanlder 
  
  """
  accession_number = kwargs['accession_number']

  target_file = f'{server_config.SEARCH_DIR}/{accession_number}.dcm'
  

  if not(os.path.exists(target_file)):
    logger.error(f'Could not find the file {accession_number} from pacs')
  else:
    logger.info(f'Recieved File successfully for study {accession_number}')

def move_and_store(dataset, *args, **kwargs):
  """
    This function is a response to a C_find moves it over to the cache.
    This means if a user searches for the same study twice on the same day, it's 
    only downloaded once

    args:
      C-Find retrun dataset dataset
      required KW:
        move_assoc: An connected and active Pynetdicom.Association object

  """
  if 'move_assoc' and 'config' in kwargs:
    move_assoc = kwargs['move_assoc']
    config     = kwargs['config']
  else:
    logger.info('config or move_assoc doesn\'t exsists')
    raise AttributeError("move_assoc and config is a required keyword")

  ae_controller.send_move(
    move_assoc, 
    config.pacs_calling,
    dataset,
    move_study_from_search_cache,
    accession_number=dataset.AccessionNumber

    )

def get_study(user, accession_number):
  """
    This function retrieves a completed study with the accession number given. 
    Note that this function does not check the cache

    Args:
      User Django-Model.User object - The User making the request
      accession_number str - The String of Accession Number eg. REGHXXXXXXXX
    Returns:
      Dataset: None - The Dataset could not be found or an Pydicom.Dataset Object. The Requested Dataset.
      pathToDataset: The path to the dataset

    Remark:
      This is overhauled version of move_from_pacs
  """
  config = user.department.config
  pacs_find_ae = ae_controller.create_find_AE(config.pacs_calling)
  pacs_move_ae = ae_controller.create_move_AE(config.pacs_calling)

  pacs_find_assoc = ae_controller.establish_assoc(
    pacs_find_ae, 
    config.pacs_ip,
    config.pacs_port,
    config.pacs_aet,
    logger
  )
  if not(pacs_find_assoc):
    return None, "Error"

  pacs_move_assoc = ae_controller.establish_assoc(
    pacs_move_ae, 
    config.pacs_ip,
    config.pacs_port,
    config.pacs_aet,
    logger )

  if not(pacs_move_assoc):
    pacs_find_assoc.release()
    logger.error('Could not etablish with pacs find assoc!')
    return None, "Error"

  find_dataset = dataset_creator.create_search_dataset('', '', '', '', accession_number )
  ae_controller.send_find(
    pacs_find_assoc,
    find_dataset,
    move_and_store,
    move_assoc=pacs_move_assoc,
    config=config )

  target_file = f'{server_config.SEARCH_DIR}/{accession_number}.dcm'

  if os.path.exists(target_file):
    return dicomlib.dcmread_wrapper(target_file), target_file
  else:
    logger.error(f'Could not find request study {accession_number}')
    return None, "Error"

def store_dicom_pacs(dicom_object, user, ensure_standart=True):
  """
  Stores a dicom object in the user defined pacs (user.department.config)
  It uses a C-store message

  Args:
    dicom_object : pydicom dataset, the dataset to be stored
    user : a django model user, the user that stores 

  KWargs:
    ensure_standart : Bool, if true the function preforms checks, that the given dicom object contains the nessesary tags for a successful
  Returns:
    Success : Bool, returns true on a success full storage, false on failed storage
    Failure Message : String, A user friendly message of what went wrong. Empty on success. 
  Raises
    Value error: If the dicom set doesn't contain required information to send
  """
  accession_number = dicom_object.AccessionNumber

  # Save the dicom file to be sent to PACS
  try_mkdir(server_config.PACS_QUEUE_DIR, mk_parents=True)
  store_file = f"{server_config.PACS_QUEUE_DIR}{accession_number}.dcm"
  
  dicomlib.save_dicom(store_file, dicom_object)

  # Write file with connection configurations
  # hey hey hey, I present the newest programming invention:
  # MULTIPLE FUNCTIONAL ARGUMENTS, no more writing a file, and opening it up 
  with open(f"{server_config.PACS_QUEUE_DIR}{accession_number}.json", "w") as fp:
    fp.write(json.dumps({
      "pacs_calling": user.department.config.pacs_calling,
      "pacs_ip": user.department.config.pacs_ip,
      "pacs_port": user.department.config.pacs_port,
      "pacs_aet": user.department.config.pacs_aet,
    }))

  # Spawn background thread to send study
  store_thread = threading.Thread(
    target=thread_store,
    args=(
      accession_number,
      server_config.PACS_QUEUE_WAIT_TIME
    )
  )
  store_thread.start()

  return True, ""


def thread_store(accession_number, wait_time, max_attempts=5):
  """
  Send a study to PACS

  Args:
    accession_number: accession number of study to send
    wait_time: time to wait before attempting to send again if failed

  Kwargs:
    max_attempts: max number of attempts to try and send to PACS

  TODO: Implement the max cap for attempts
  NOTE: Adding a cap on the number of attempts might be a bad idea,
        think if PACS is down for the whole day and the cap runs out. 
        Then a lot of studies are going to get stuck in the queue folder, 
        and aren't sent to PACS until the entire server is reset.
  """
  # Load study and connection configuration - if the files cannot be found don't send
  ds_file = f"{server_config.PACS_QUEUE_DIR}{accession_number}.dcm"
  conf_file = f"{server_config.PACS_QUEUE_DIR}{accession_number}.json"

  if not os.path.exists(ds_file) or not os.path.exists(conf_file):
    return

  with open(conf_file, "r") as fp:
    conf = json.loads(fp.read())

  ds = dicomlib.dcmread_wrapper(ds_file)

  # Send study to PACS
  is_sent = False

  while not is_sent:
    ae = AE(ae_title=conf["pacs_calling"])
    ae.add_requested_context('1.2.840.10008.5.1.4.1.1.7', transfer_syntax='1.2.840.10008.1.2.1')
    assoc = ae.associate(
      conf["pacs_ip"],
      int(conf["pacs_port"]),
      ae_title=conf["pacs_aet"]
    )

    if assoc.is_established:
      status = assoc.send_c_store(ds)
      if status.Status == 0x0000:
        is_sent = True
    
    if not is_sent:
      time.sleep(wait_time)

  # Clean up
  os.remove(ds_file)
  os.remove(conf_file)


def send_queue_to_PACS():
  """
  Spawn threads for sending all studies in the queue folder to PACS
  This should be called on start up of the server, so the missing
  studies can be correctly send to PACS.
  """
  for dcm_file in glob.glob(f"{server_config.PACS_QUEUE_DIR}*.dcm"):
    accession_number = dcm_file.split(".")[-2].split("/")[-1]

    # print(f"Spawning PACS send thread for: {accession_number}")

    store_thread = threading.Thread(
      target=thread_store,
      args=(
        accession_number,
        server_config.PACS_QUEUE_WAIT_TIME
      )
    )
    store_thread.start()


def start_scp_server(ae_title):
  """
  Problems:
    The server host multiple AE titles 
      TEMP SOLUTION:
        Accepts all AE title
    Shutting down the server is difficult, since it's on another thread
    server_instance.shutdown() needs to becalled for normal shutdown 
      TEMP SOLUTION:
        ONE DOES NOT SIMPLY SHUTDOWN THE SERVER aka TODO for a designer,
          Potential Solution:
            Create Global Variable in server config and set it to none
            When Creating Server overwrite global Variable with server instance
            THIS MAY NOT WORK, I*M A SHIT PYTHON PROGRAMMER
    Saving a file, While it's clear that it should be saved in the search_dir.
    However Saving in subdirectories are difficult 
  """
  logger = log_util.get_logger(__name__)
  logger.info('Starting Server')
  def on_store(dataset, context, info):
    """
    Stores a Files upon a C-store


      Returns
        0x0000 - success code for successful store 

    
      Retried due to retried functionality of Pynetdicom v 1.4.0
    """
    #logger.info(f"Recieved C-STORE with ID:{info['parameters']}")
    #logger.info(f"C-Store Originated from:{info['parameters']}")
    
    if 'AccessionNumber' in dataset:

      filename = f'{dataset.AccessionNumber}.dcm'
      fullpath = server_config.SEARCH_DIR + filename

      dicomlib.save_dicom(fullpath, dataset)

      return 0x0000
    else:
      logger.warn('Recieved invalid dicomobject')
      returndataset = Dataset()
      returndataset.Status = 0xCAFE
      returndataset.add_new(0x00000902, 'LO', 'This service cannot store DICOM objects without AccessionNumber')
      return returndataset

  def on_move(dataset, move_aet, context, info):
    """
      C-Move is unsupported by our Application as we do not have access to the list

      Retried due to retried functionality of Pynetdicom v 1.4.0
    """
    logger.info('Recieved C-move')
    logger.info('\n')
    logger.info(dataset)
    logger.info('\n')
    logger.info(move_aet)
    logger.info('\n')
    logger.info(context)
    logger.info('\n')
    logger.info(info)
    logger.info('\n')

    return 0xA801

  def on_c_move_event(event):
    """
      C-Move is not supportted by our service, since it's not connected any dicom network

      This function is where you need to update, if this is changing.
    """
    logger.info('Recieved C-Move event')
    try:
      logger.info(f'Move Data Recieved:\n{event.dataset}')
      logger.info(f'destination is:{event.move_destination}')
    except:
      logger.info(f'Could not log dataset or move_destination')
    response_dataset = pydicom.Dataset()

    response_dataset.Status = 0xA801
    response_dataset.add_new(0x00000902, 'LO', 'This service cannot store DICOM objects without AccessionNumber')

    return response_dataset

  def on_c_store_event(event):
    logger.info('Recieved C-Store Event')
    try:
      retrieved_dataset           = event.dataset
      retrieved_dataset.file_meta = event.file_meta
    
    except:
      return_dataset = pydicom.Dataset()
      return_dataset.Status = 0xC123
      returndataset.add_new(0x00000902, 'LO', 'Could not load retrieve Dataset')

      return return_dataset
    # Infomation Retrieved
    # Availble vars retrieved_dataset, retrieved_meta_info
    
    #logger.info(f'Dataset:\n {retrieved_dataset}')

    if 'AccessionNumber' in retrieved_dataset:
      if 0x00230010 in retrieved_dataset and retrieved_dataset.Modality == 'OT':
        filename = f'{retrieved_dataset.AccessionNumber}.dcm'
        fullpath = server_config.SEARCH_DIR + filename
        dicomlib.save_dicom(fullpath, retrieved_dataset)

      return 0x0000

    else:
      return_dataset = pydicom.Dataset()
      return_dataset.Status = 0xCAFE
      return_dataset.add_new(0x00000902, 'LO', 'This service cannot store DICOM objects without AccessionNumber') 
      return response_dataset


  def sop_common_handler(event):
    logger.info(event.name)
    logger.info(event.description)
    logger.info(event.assoc)
    logger.info(event.items)

  def sop_extended_handler(event):
    logger.info(event.name)
    logger.info(event.description)
    logger.info(event.assoc)
    logger.info(event.app_info)

  def log_event_handler(event):
    logger.info('\n New Event Logged!\n')
    logger.info(event.name)
    logger.info(event.description)
    logger.info(event.assoc)

  def connection_open_handler(event):
    """
      Logs Relevant information from a connection open event.

      Args:
        Event - a evt.EVT_CONN_OPEN
    """
    try:
      logger.info(f"SCP Opened Connecition with {event.address[0]}")
    except:
      logger.info(f"Could Not log Ip address of event over")

  event_handlers = [
    #(evt.EVT_ASYNC_OPS, log_event_handler),
    #(evt.EVT_SOP_COMMON, sop_common_handler),
    #(evt.EVT_SOP_EXTENDED, sop_extended_handler),
    (evt.EVT_USER_ID, log_event_handler), 
    (evt.EVT_C_STORE, on_c_store_event),
    (evt.EVT_C_MOVE, on_c_move_event), 
    # No Response
    (evt.EVT_ABORTED, log_event_handler),
    (evt.EVT_CONN_OPEN, connection_open_handler),
    (evt.EVT_REQUESTED, log_event_handler),
  ]

  try_mkdir(server_config.SEARCH_DIR)

  server_ae = AE(ae_title=ae_title)
  server_ae.supported_contexts = StoragePresentationContexts
  #
  #server_ae.on_c_store = on_store 
  #server_ae.on_c_move = on_move

  server_instance = server_ae.start_server(('', 104), block=False, evt_handlers=event_handlers) # Production
  # server_instance = server_ae.start_server(('', 11112), block=False, evt_handlers=event_handlers) # Testing / Debugging

  return server_instance

def search_query_pacs(config, name="", cpr="", accession_number="", date_from="", date_to=""):
  """
  Return list of responses, None if PACS connection failed
  """
  # Construct Search Dataset
  search_dataset = dataset_creator.create_search_dataset(
    name,
    cpr, 
    date_from,
    date_to, 
    accession_number
  ) 

  # Establish association to PACS
  association = ae_controller.connect(
    config.pacs_ip,
    int(config.pacs_port),
    config.pacs_calling, 
    config.pacs_aet,
    ae_controller.FINDStudyRootQueryRetrieveInformationModel
  )

  # Send find query and process successful responses
  response_list = [ ]
  def process_incoming_dataset(dataset, *args, **kwargs):
    if 'logger' in kwargs:
      logger = kwargs['logger']
    try:
      response_list.append({
        'accession_number': dataset.AccessionNumber,
        'name'            : formatting.person_name_to_name(str(dataset.PatientName)),
        'cpr'             : formatting.format_cpr(dataset.PatientID),
        'date'            : formatting.format_date(dataset.StudyDate)
      })
    except Exception as e:
      logger.info(f"Failed to process incoming search dataset, got exception {e}")

  try:
    ae_controller.send_find(
      association,
      search_dataset,
      process_incoming_dataset,
      logger=logger
    )
  except ValueError:
    logger.error(f"Failed to establish association to PACS with parameters:\npacs_ip: {config.pacs_ip}, pacs_port: {config.pacs_port}, pacs_calling: {config.pacs_calling}, pacs_aet: {config.pacs_aet}")
    return None

  association.release()

  logger.info(f'Returning search list of {len(response_list)}')

  return response_list


def get_history_from_pacs(dataset, active_objects_path):
  """
  Retrieves information historical data about a user from pacs.
  This function doesn't save anything

  Args:
    cpr: string The cpr number without a string 
    age: Datetime object with day of birth

  Returns:
    date_list:            A datetime-list. The n'th element is a datetime object with time of examination. The lenght is 'm'
    age_list:             A float list. Element is calculated age at time of examination. The lenght is 'm'
    clearence_norm_list:  A float list. The n'th element is float
  Notes:
    This function doesn't save anything and cleans up after it-self
  """
  
  #Init 
  age_list            = []
  clearence_norm_list = []
  date_list           = []
  history_sequence    = []

  birthday = dataset.PatientBirthDate

  #Get all file paths for the Accession number
  curr_dicom_path = f"{active_objects_path}{dataset.AccessionNumber}/{dataset.AccessionNumber}.dcm"
  dicom_filepaths = glob.glob(f'{active_objects_path}{dataset.AccessionNumber}/*.dcm')
  #Filter the already opened dataset out
  history_filepaths = filter(lambda x: x != curr_dicom_path, dicom_filepaths)
  #Iterate through the datasets
  for history_filepath in history_filepaths:
    #Open the dataset
    
    history_dataset = dicomlib.dcmread_wrapper(history_filepath)
    #Create History dataset for history datasets
    try:
      date_of_examination = datetime.datetime.strptime(history_dataset.StudyDate,'%Y%m%d')
      age_at_examination = (date_of_examination - birthday).days / 365
      
      age_list.append(age_at_examination)
      date_list.append(date_of_examination)
      clearence_norm_list.append(history_dataset.normClear)

      #Dataset for dicom
      sequence_dataset = Dataset()
      sequence_dataset.AccessionNumber  = history_dataset.AccessionNumber
      sequence_dataset.StudyDate        = history_dataset.StudyDate
      sequence_dataset.PatientSize      = history_dataset.PatientSize
      sequence_dataset.PatientWeight    = history_dataset.PatientWeight
      #Private tags 
      sequence_dataset.clearance        = history_dataset.clearance 
      sequence_dataset.normClear        = history_dataset.normClear 
      sequence_dataset.ClearTest        = history_dataset.ClearTest 
      sequence_dataset.injTime          = history_dataset.injTime   
      history_sequence.append(sequence_dataset)
    except AttributeError as E:
      logger.error(f'Sequence dataset {history_filepath} has invalid format with {E}')

  dicomlib.fill_dicom(dataset, dicom_history=history_sequence)
  
  return date_list, age_list, clearence_norm_list


def get_history_for_csv(
  user,
  date_bounds                 = (datetime.date(2019,7,1), datetime.date(2100,1,1)),
  clearance_bounds            = (0.,200.),
  clearance_normalized_bounds = (0.,200.),
  thin_fact_bounds            = (0.,25000.),
  standard_bounds             = (0.,100000.),
  injection_weight_bounds     = (0.,2.),
  height_bounds               = (0., 250.),
  weight_bounds               = (0., 250.),
  age_bounds                  = (0., 125),
  cpr_bounds                  = '',
  method_bounds               = [],
  gender_bounds               = ['M','F','O']
  ):
  """
  Retrives all studies and processes them to match up with the following filters

  KWargs:
    date_bounds                 : tuple of date datetime objects, if none, then no filtering will be done on the object
    clearance_bounds            : tuple of floats, removes all studies where tag 0x00231012 not in range of the tuple. First argument is smaller than the secound argument
    clearance_normalized_bounds : tuple of floats, removes all studies where tag 0x00231014 not in range of the tuple. First argument is smaller than the secound argument
    thin_fact_bounds            : tuple of floats, removes all studies where tag 0x00231028 not in range of the tuple. First argument is smaller than the secound argument
    standard_bounds             : tuple of floats, removes all studies where tag 0x00231024 not in range of the tuple. First argument is smaller than the secound argument
    injection_weight_bounds     : tuple of floats, removes all studies where tag 0x0023101A not in range of the tuple. First argument is smaller than the secound argument
    height_bounds               : tuple of floats, removes all studies where tag 0x0023101A not in range of the tuple. First argument is smaller than the secound argument
    weight_bounds               : tuple of floats, removes all studies where tag 0x0023101A not in range of the tuple. First argument is smaller than the secound argument
    age_bounds                  : tuple of floats, removes all studies where tag 0x0023101A not in range of the tuple. First argument is smaller than the secound argument
    cpr_bounds                  : string, filters only a after a specific person, if empty removes test patients
    method_bounds               : string list, removes all studies where tag 0x0008103E is 
    gender_bounds               : char list, removes all studies, where the gender is not on the list. Valid Characters are M and F

  Raises: 
    ValueError : Whenever a keyword tuple first argument is greater than the secound argument 
  """
  #Helper Functions 
  #Check bounds
  def check_bounds(a_tuple):
    if a_tuple[0] > a_tuple[1]:
      raise ValueError('Invalid bounds, secound argument of each tuple must be greater than the first.')

  def in_bounds(a_tuple, a_value):
    return a_tuple[0] <= a_value and a_value <= a_tuple[1]  

  def check_study(study): 
    #
    birthdate = datetime.datetime.strptime(study.PatientBirthDate, '%Y%m%d')
    age_in_years = int((datetime.datetime.now() - birthdate).days / 365)
    study_date = datetime.datetime.strptime(study.StudyDate,'%Y%m%d').date()

    bounds = (
      (date_bounds, study_date),
      (clearance_bounds, study.clearance),
      (clearance_normalized_bounds, study.normClear),
      (thin_fact_bounds, study.thiningfactor),
      (standard_bounds, study.stdcnt),
      (injection_weight_bounds, study.injWeight),
      (height_bounds, study.PatientSize * 100.0),
      (weight_bounds, study.PatientWeight),
      (age_bounds, age_in_years),
    )
    
    # bounds checking
    valid_study = True
    for bound, val in bounds:
      valid_study &= in_bounds(bound, val)

    # Additional bounds checking
    valid_study &= cpr_bounds.replace('-','') == study.PatientID
    valid_study &= study.PatientSex in gender_bounds
    if not method_bounds:
      valid_study &= study.StudyDescription in method_bounds

    return valid_study

  def format_dicom(dicom_object, taglist):
    def helper(ds, tag):
      if tag in ds:
        return str(ds[tag].value)
      else :
        return ''
      
    returnlist = []

    for tag in taglist:
      returnlist.append(helper(dicom_object, tag))
    
    return returnlist

  # End Helper Functions

  ae_title = user.department.config.pacs_calling

  bounds = (
    date_bounds,
    clearance_bounds,
    thin_fact_bounds,
    standard_bounds,
    injection_weight_bounds,
    height_bounds,
    weight_bounds,
    age_bounds,
  )
  
  for bound in bounds:
    check_bounds(bound)

  if None != formatting.check_cpr(cpr_bounds):
    raise ValueError('Invalid Cpr number')

  if not(gender_bounds in [['M'], ['F'], ['O'], ['M','F'], ['M','O'], ['F','O'] ,['M','F','O'] ]):
    raise ValueError('Invalids Genders')
  #End checking bounds

  find_ae = pynetdicom.AE(ae_title=ae_title)
  move_ae = pynetdicom.AE(ae_title=ae_title)

  #Add different presentation contexts for the AE's
  FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.1'
  MOVEStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2'

  find_ae.add_requested_context(FINDStudyRootQueryRetrieveInformationModel)
  move_ae.add_requested_context(MOVEStudyRootQueryRetrieveInformationModel)

  #Associates

  #Note that due to some unknown bugs, pacs is not happy make the same association handling both move and finds at the same time, thus we make two associations
  find_assoc = find_ae.associate(
    user.department.config.pacs_ip,
    int(user.department.config.pacs_port),
    ae_title=user.department.config.pacs_calling
  )

  move_assoc = move_ae.associate(
    user.department.config.pacs_ip,
    int(user.department.config.pacs_port),
    ae_title=user.department.config.pacs_calling
  )

  studies = []

  if find_assoc.is_established and move_assoc.is_established:
    find_query_dataset = dataset_creator.create_search_dataset(
      date_from = date_bounds[0].strftime("%Y%m%d"),
      date_to   = date_bounds[1].strftime("%Y%m%d")
    )

    #This retrives all studies from pacs
    find_response = find_assoc.send_c_find(
      find_query_dataset,
      query_model='S'
    )

    for find_status, find_response_dataset in find_response:
      successfull_move = False
      move_response = move_assoc.send_c_move(find_response_dataset, ae_title, query_model='S')
      for (status, identifier) in move_response:
        if status.Status == 0x0000:
          # Status code for C-move is successful
          logger.info('C-move successful')
          successfull_move = True
        elif status.Status == 0xFF00:
          #We are not done, but shit have not broken down
          pass
        else:
          logger.warn('C-Move move opration failed with Status code:{0}'.format(hex(status.Status)))
      #C-move done for the one response
      file_location = f'{server_config.SEARCH_DIR}/{find_dataset.AccessionNumber}.dcm'
      if successfull_move and os.path.exists(file_location) :
        study = dicomlib.dcmread_wrapper(f'{server_config.SEARCH_DIR}/{find_response_dataset.AccessionNumber}')
        os.remove(file_location)
        try:
          #Here is where the indiviual study handling happens
          if check_study(study):
            studies.append(studies)
          else:
            pass #Study Was not part search critie
        except: #TODO error handling
          logger.error(f'Error in handling:\n {study}')
      else:
        logger.info(f'Could not successfully move {find_response_dataset.AccessionNumber}')

    # Finallize Association
    find_assoc.release()
    move_assoc.release()
  else:
    logger.error('Could not connect to pacs')
    #While unlikely a bug could be there
    if find_assoc.is_established:
      find_assoc.release()
    if move_assoc.is_established:
      move_assoc.release()

  # TODO: Make the below code use the export_dicom function from dicomlib
  #Handling of studies
  #Studies at this point contains all valid studies given by the function input
  #This part is the csv

  today = datetime.datetime.today()
  filename = f'gfr_data_{today.strftime("%Y%m%d")}.csv'
  with open(filename, mode='w', newline = '') as csv_file:
    
    csv_writer = csv.writer(
      csv_file,
      delimiter=',',
      quotechar=''
    )
    
    header_tags = [
      ("Navn",                    0x00100010),
      ("CPR",                     0x00100020),
      ("Alder",                   0x00100010),
      ("Højde",                   0x00101020),
      ("Vægt",                    0x00101030),
      ("Køn",                     0x00100040),
      ("Dato",                    0x00080020),
      ("Krops overfalde metode",  0x00231011),
      ("Clearance",               0x00231012),
      ("Clearance Normalized",    0x00231014),
      ("Injektions Tidspunkt",    0x00231018),
      ("Injektions vægt",         0x0023101A),
      ("Sprøjte Vægt før",        0x0023101B),
      ("Sprøjte Vægt Efter",      0x0023101C),
      ("Standard",                0x00231024),
      ("Thining Factor",          0x00231028),
    ]
    sequnce_header = [
      "Prøve 1 Værdi",  "Prøve 1 tidpunkt",
      "Prøve 2 Værdi",  "Prøve 2 tidpunkt",
      "Prøve 3 Værdi",  "Prøve 3 tidpunkt",
      "Prøve 4 Værdi",  "Prøve 4 tidpunkt",
      "Prøve 5 Værdi",  "Prøve 5 tidpunkt",
      "Prøve 6 Værdi",  "Prøve 6 tidpunkt"
    ]

    sequence_tags = [0x00231021, 0x00231022]

    textrow = [header_tag[0] for header_tag in header_tags] + sequnce_header 
    csv_writer.writerow(textrow)

    taglist = [atuple[1] for atuple in header_tags]
    for study in studies:
      
      datarow = format_dicom(study, taglist)
      seq_strs = []
      if 0x00231020 in study:
        for seq_item in study[0x00231020]:
          strs = format_dicom(seq_item, sequence_tags)
          
          seq_strs += strs

      datarow += seq_strs

      csv_writer.writerow(datarow)          


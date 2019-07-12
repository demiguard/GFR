import pydicom, pynetdicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict
from pynetdicom import AE, StoragePresentationContexts, evt
import os, logging
import sys
import shutil
import glob
import datetime
import calendar
import numpy
import pandas
import random

from .. import dicomlib, dirmanager, dataset_creator
from .. import server_config
from ..clearance_math import clearance_math
from .. import examination_info
from ..examination_info import ExaminationInfo
from .. import formatting
from .query_executer import execute_query

logger = logging.getLogger()

def move_from_pacs(user, accession_number):
  """
    

    Returns:
      None or Dataset - The dataset is always single
  """
  # # # Get file from pacs # # #
  find_datasets = []
  for stationName in server_config.STATION_NAMES:
    find_dataset = dataset_creator.create_search_dataset(
      '', #Name
      '', #CPR
      '', #Date_from
      '', #Date_to
      accession_number,
      stationName
    )
    find_datasets.append(find_dataset)


  find_ae = AE(ae_title=server_config.SERVER_AE_TITLE)
  FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.1'
  find_ae.add_requested_context(FINDStudyRootQueryRetrieveInformationModel)

  move_ae = AE(ae_title=server_config.SERVER_AE_TITLE)
  MOVEStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.2'
  move_ae.add_requested_context(MOVEStudyRootQueryRetrieveInformationModel) 

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
  if find_assoc.is_established and move_assoc.is_established:
    
    find_dataset_from_response = []
    for find_dataset in find_datasets:
      find_response = find_assoc.send_c_find(find_dataset, query_model='S')
      for (status, dataset_from_find) in find_response:
        # Error Checking
        if status.Status == 0xC001:
          logger.warn(f"""
            C-FIND failed with dataset: 
            {find_dataset}
          """)
          try:
            move_assoc.release()          
            find_assoc.release()
          except:
            pass
          return None
          # Extract available data 
        if dataset_from_find != None:
          find_dataset_from_response.append(dataset_from_find)
    
    if len(find_dataset_from_response) > 1:
      #Soooo somehow we got more than one response to a unique AccessionNumber?
      logger.warn(f"""
      Move_from_pacs got multiple responses to AccessionNumber: {rigs_nr}

      The responses was:
        {find_dataset_from_response} 
      
      """)
    elif len(find_dataset_from_response) == 0:
      Logger.info(f"Could not find any study under {rigs_nr}")
      find_assoc.release()
      move_assoc.release()
      return None

    #Takes the first dataset. We can do this because len > 0
    move_query_dataset = find_dataset_from_response[0]
    
    successfull_move = False
    move_response = move_assoc.send_c_move(
      move_query_dataset,
      server_config.SERVER_AE_TITLE,
      query_model='S'
    )
    for (status, identifier) in move_response:
      if status.Status == 0x0000:
        # We are successful
        logger.info('C-move successful')
        successfull_move = True
      elif status.Status == 0xFF00:
        #We are not done, but shit have not broken down
        pass
      else:
        logger.warn('C-Move move opration failed with Status code:{0}'.format(hex(status.Status)))
    assoc.release()
  else:
    logger.warn('Move_from_pacs could not connect to pacs')
    return None

  file_src = f'{server_config.SEARCH_DIR}{accession_number}.dcm'
  if successfull_move and os.path.exists(file_src):
    dataset = dicomlib.dcmread_wrapper(file_src)
    os.remove(file_src) # Deletes the file, because we are done with it, and if the user want the page again, they have 
    return dataset
  else:
    logger.warn('Mismatching matching Accession number, Perhaps Pacs doesn\'t have the requested file? Maybe you have incorrect info')
    return None

def get_from_pacs(user, rigs_nr, cache_dir, resp_path="./rsp/"):
  """
  Retreives an examination from a dicom database (DCM4CHEE/PACS)

  Args:
    user: currently logged in user
    rigs_nr: rigs number of patient to retreive
    cache_dir: directory for cached dicom objects (TODO: THIS MIGHT JUST BE THE hospital FROM THE user, IF SO CHANGE IT)

  Returns:
    Dicom object for the retreived patient, otherwise None

  Remarks:
    The below lines provides commandline examples for manually executing the queries:
    findscu -S 127.0.0.1 11112 -aet RH_EDTA -aec TEST_DCM4CHEE -k 0008,0050="<rigs_nr>" -k 0008,0052="STUDY" -k 0010,0020 -k 0020,000D -X
    getscu -P 127.0.0.1 11112 -k 0008,0052="STUDY" -k 0010,0020="<patient id>" -k 0020,000D="<study instance uid>" -aec TEST_DCM4CHEE -aet RH_EDTA -od .
  """
  BASE_FIND_QUERY_PATH = resp_path + "base_find_query.dcm"
  BASE_IMG_QUERY_PATH = resp_path + "base_get_image.dcm"
  
  logger.info('Get from pacs is called')


  # Insert AccessionNumber into query file
  find_query = dicomlib.dcmread_wrapper(BASE_FIND_QUERY_PATH)
  find_query.AccessionNumber = rigs_nr
  find_query.save_as(BASE_FIND_QUERY_PATH)

  # Construct and execute command
  find_query = [
    server_config.FINDSCU,
    '-S',
    user.department.config.pacs_ip,
    user.department.config.pacs_port,
    '-aet',
    user.department.config.pacs_calling,
    '-aec',
    user.department.config.pacs_aet,
    BASE_FIND_QUERY_PATH,
    '-X',
    '-od',
    resp_path
  ]

  # TODO: Add error handling of failed queries (Update execute_query first to return exit-code)
  out = execute_query(find_query)

  # Use first resp
  rsp_paths = glob.glob(resp_path + 'rsp*.dcm')
  if len(rsp_paths) != 0:
    rsp_path = rsp_paths[0]
  else:
    return None

  # Extract Patient ID and Study Instance UID from respons
  patient_rsp = dicomlib.dcmread_wrapper(rsp_path)
  patient_id = patient_rsp.PatientID
  si_uid = patient_rsp.StudyInstanceUID

  os.remove(rsp_path)

  # Insert patient id and study instance uid into image query file
  img_query = dicomlib.dcmread_wrapper(BASE_IMG_QUERY_PATH)
  img_query.PatientID = patient_id
  img_query.StudyInstanceUID = si_uid
  img_query.save_as(BASE_IMG_QUERY_PATH)

  # Construct and execute image query
  img_query = [
    server_config.GETSCU,
    '-P',
    user.department.config.pacs_ip,
    user.department.config.pacs_port,
    BASE_IMG_QUERY_PATH,
    '-aet',
    user.department.config.pacs_calling,
    '-aec',
    user.department.config.pacs_aet,
    '-od',
    resp_path
  ]

  execute_query(img_query)

  # Open resp obj and return
  img_rsp_paths = list(filter(lambda x: 'SC' in x, os.listdir(resp_path)))
  if len(img_rsp_paths) != 0:
    img_rsp_path = resp_path + img_rsp_paths[0]
  else:
    return None

  # Move found object into cache
  cache_path = cache_dir + rigs_nr + '.dcm'
  
  os.rename(img_rsp_path, cache_path)

  obj = dicomlib.dcmread_wrapper(cache_path)
  return obj


def get_examination(user, rigs_nr, resp_dir):
  """
  Retreive examination information based on a specified RIGS nr.

  Args:
    rigs_nr: RIGS nr of examination

  Returns:
    ExaminationInfo instance containing examination information for the specified
    RIGS nr.
  """
  # Read after dictionary update
  try:
    obj = dicomlib.dcmread_wrapper(f'{resp_dir}{rigs_nr}.dcm')
  except FileNotFoundError:
    # Get object from DCM4CHEE/PACS Database
    obj = move_from_pacs(user, rigs_nr)

  return examination_info.deserialize(obj)


def store_in_pacs(user, obj_path):
  """
  Stores a given study in the PACS database

  Retired function use store_dicom_pacs instead

  Args:
    user: currently logged in user
    obj_path: path to object to store
  """  
  # Construct query and store
  store_query = [
    server_config.STORESCU,
    '-aet',
    user.department.config.pacs_calling,
    '-aec',
    user.department.config.pacs_aet,
    user.department.config.pacs_ip,
    user.department.config.pacs_port,
    obj_path
  ]
  
  out = execute_query(store_query)

  return (out != None)

def store_dicom_pacs(dicom_object, user, ensure_standart = True ):
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
  ae = AE(ae_title=server_config.SERVER_AE_TITLE)
  ae.add_requested_context('1.2.840.10008.5.1.4.1.1.7', transfer_syntax='1.2.840.10008.1.2.1')
  assoc = ae.associate(
    user.department.config.pacs_ip,
    int(user.department.config.pacs_port),
    ae_title=user.department.config.pacs_aet
  )

  if assoc.is_established:
    status = assoc.send_c_store(dicom_object)
    if status.Status == 0x0000:
      return True, ''
    elif status.Status == 0x0124:
      return False, 'Duplikeret Argument'
    elif status.Status >= 0xA700 and status.Status <= 0xA7FF:
      return False, 'Pacs har ikke hukommelse til at gemme undersøgelsen'
    else:
      return False, 'Fejlede at gemme i pacs med ukendt fejlkode:{0}'.format(hex(status.Status))
  else: 
    return False , 'Kunne ikke forbinde til pacs'
  
def start_scp_server():
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
  logger = logging.getLogger()
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
    
    if 'AccessionNumber' in retrieved_dataset:
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

  dirmanager.check_combined_and_create(server_config.SEARCH_DIR)

  server_ae = AE(ae_title=server_config.SERVER_AE_TITLE)
  server_ae.supported_contexts = StoragePresentationContexts
  #
  #server_ae.on_c_store = on_store 
  #server_ae.on_c_move = on_move

  server_instance = server_ae.start_server(('', 104), block=False, evt_handlers=event_handlers)

  return server_instance

def search_query_pacs(user, name="", cpr="", accession_number="", date_from="", date_to=""):
  response_list = []

  # Construct Search Dataset
  search_datasets = []
  for stationName in server_config.STATION_NAMES:
    search_datasets.append(dataset_creator.create_search_dataset(
      name,
      cpr, 
      date_from, 
      date_to, 
      accession_number, 
      stationName)
    )

  logger.info(f"Executing search query with paramenters: name='{name}', cpr='{cpr}', date_from='{date_from}', date_to='{date_to}', accession_number='{accession_number}'")

  # Construct AE
  ae = AE(ae_title=server_config.SERVER_AE_TITLE)
  ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.1')

  # Connect with AE
  assoc = ae.associate(user.department.config.pacs_ip, int(user.department.config.pacs_port), ae_title=user.department.config.pacs_aet)
  
  if assoc.is_established:
    # Make Search Request
    for search_dataset in search_datasets:
      response = assoc.send_c_find(search_dataset, query_model='S')
      for (status, dataset) in response:
        if status.Status == 0xFF00:
          logger.info(dataset)

          exam_obj = examination_info.deserialize(dataset)

          response_list.append(exam_obj)
        elif status.Status == 0x0000:
          # Operation successfull
          continue
        else:
          logger.info('Error, recieved status:{0}\n{1}'.format(hex(status.Status), status))
      else:
        logger.warn('Connection to pacs failed!')

    assoc.release()
  return response_list


def get_history_from_pacs(cpr, birthday, user):
  """
    Retrieves information historical data about a user from pacs.
    This function doesn't save anything

    Args:
      cpr: string The cpr number without a string 
      age: Datetime object with day of birth

    Returns:
      date_list:            A datetime-list. The n'th element is a datetime object with time of examination. The lenght is 'm'
      age_list:             A float list. The n'th element is calculated age at time of examination. The lenght is 'm'
      clearence_norm_list:  A float list. The n'th element is float
    Notes:
      This function doesn't save anything and cleans up after it-self
  """
  
  #Init 
  date_list           = []
  age_list            = []
  clearence_norm_list = []



  #Create Assosiation to pacs
  find_ae = pynetdicom.AE(ae_title=user.department.config.pacs_calling)
  move_ae = pynetdicom.AE(ae_title=user.department.config.pacs_calling)
  FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.1'
  find_ae.add_requested_context(FINDStudyRootQueryRetrieveInformationModel) #Contest for C-FIND
  MOVEStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.2'
  move_ae.add_requested_context(MOVEStudyRootQueryRetrieveInformationModel) 
  
  #Create the dataset for a C-FIND
  find_datasets = []
  for station_name in server_config.STATION_NAMES:
    dataset_creator.create_search_dataset(
      '', #Name
      cpr, #CPR
      '', #Date_from
      '', #date_to
      '', #Accession Number
      station_name #StationName
    )
  
  #Make a C-FIND to pacs
  find_assoc = find_ae.associate(
    user.department.config.pacs_ip,
    int(user.department.config.pacs_port),
    ae_title=user.department.config.pacs_aet)

  move_assoc = move_ae.associate(
    user.department.config.pacs_ip,
    int(user.department.config.pacs_port),
    ae_title=user.department.config.pacs_aet
  )

  if find_assoc.is_established and move_assoc.is_established:
    for find_dataset in find_datasets:
      find_response = find_assoc.send_c_find(find_dataset, query_model='S')
      for (find_status, find_response_dataset) in find_response:
        if find_status.Status == 0xFF00:
          #Create Dataset to C-MOVE
          accession_number = find_response_dataset.AccessionNumber

          #For each response make a C-MOVE to myself
          move_response = move_assoc.send_c_move(
            find_response_dataset,
            user.department.config.pacs_calling,
            query_model='S'
          )
          for (move_status, identifyer) in move_response:
            if move_status.Status == 0x0000:
              filename = f'{server_config.SEARCH_DIR}{accession_number}.dcm'
              #Open the DCM file
              logger.info(f'Search File, Filename: {filename}')
              try:
                move_response_dataset = dicomlib.dcmread_wrapper(filename)
                #Read values of Clearence Normalized and date of examination into a return list
                date_of_examination = datetime.datetime.strptime(move_response_dataset.StudyDate,'%Y%m%d')
                date_list.append(date_of_examination)
                age_at_examination = (date_of_examination - birthday).days / 365
                age_list.append(age_at_examination)
                clearence_norm_list.append(float(move_response_dataset.normClear))
                #Delete the file
                logger.info(f'Deleteing File: {filename}')
                os.remove(filename)
              except Exception as E:
                logger.warn(f'Error handling {accession_number} with {E}')      
            else:
              logger.warn(f'Move Response code:{move_status.Status}')
        elif find_status.Status == 0x0000:
          logger.info(f"""Successfull gathered history to be:
            date_list:{date_list}
            age_list:{age_list}
            clearence_normalized_list:{clearence_norm_list}""")
        else: 
          logger.warn(f""" Unexpected Status code:{find_status.Status}""")
    #If statement done
    find_assoc.release()
    move_assoc.release()
  else:
    logger.warn('Could not connect to pacs')
  #Return
  return date_list, age_list, clearence_norm_list

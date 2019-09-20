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

from main_page.libs.dirmanager import try_mkdir
from .. import dicomlib, dataset_creator
from .. import server_config
from ..clearance_math import clearance_math
from .. import examination_info
from ..examination_info import ExaminationInfo
from .. import formatting


logger = logging.getLogger()


def move_from_pacs(user, accession_number):
  """
    Returns:
      None or Dataset - The dataset is always single
  """
  # # # Get file from pacs # # #
  find_dataset = dataset_creator.create_search_dataset(
    '', #Name
    '', #CPR
    '', #Date_from
    '', #Date_to
    accession_number
  )    

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
      logger.warn(f"Move_from_pacs got multiple responses to AccessionNumber: {rigs_nr}. The responses was: {find_dataset_from_response}")
    elif len(find_dataset_from_response) == 0:
      logger.info(f"Could not find any study under {rigs_nr}")
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
    find_assoc.release()
    move_assoc.release()
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
    
    logger.info(f'Dataset:\n {retrieved_dataset}')

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
  find_dataset = dataset_creator.create_search_dataset(
      name,
      cpr, 
      date_from, 
      date_to, 
      accession_number
    )  

  logger.info(f"{user} is Executing search query with paramenters: name='{name}', cpr='{cpr}', date_from='{date_from}', date_to='{date_to}', accession_number='{accession_number}'")

  # Construct AE
  ae = AE(ae_title=server_config.SERVER_AE_TITLE)
  ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.1')

  # Connect with AE
  assoc = ae.associate(user.department.config.pacs_ip, int(user.department.config.pacs_port), ae_title=user.department.config.pacs_aet)
  
  if assoc.is_established:
    # Make Search Request
    response = assoc.send_c_find(find_dataset, query_model='S')
    for (status, dataset_from_response) in response:
      if status.Status == 0xFF00:
        exam_obj = examination_info.deserialize(dataset_from_response)

        response_list.append(exam_obj)
      elif status.Status == 0x0000:
        # Operation successfull
        continue
      else:
        logger.info('Error, recieved status:{0}\n{1}'.format(hex(status.Status), status))
    assoc.release()
  else:
    logger.warn('Connection to pacs failed!')

  return response_list


def get_history_from_pacs(dataset, cpr : str, birthday : str, user):
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
  history_datasets     = []

  birthday = datetime.datetime.strptime(birthday,'%Y-%m-%d')
  #Create Assosiation to pacs
  find_ae = pynetdicom.AE(ae_title=user.department.config.pacs_calling)
  move_ae = pynetdicom.AE(ae_title=user.department.config.pacs_calling)
  FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.1'
  find_ae.add_requested_context(FINDStudyRootQueryRetrieveInformationModel) #Contest for C-FIND
  MOVEStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.2'
  move_ae.add_requested_context(MOVEStudyRootQueryRetrieveInformationModel) 
  
  #Create the dataset for a C-FIND
  find_dataset = dataset_creator.create_search_dataset(
      '', #Name
      cpr, #CPR
      '', #Date_from
      '', #date_to
      '' #Accession Number
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
        for move_status, _ in move_response:
          if move_status.Status == 0x0000:
            filename = f'{server_config.SEARCH_DIR}{accession_number}.dcm'
            #Open the DCM file
            logger.info(f'Search File, Filename: {filename}')
            try:
              move_response_dataset = dicomlib.dcmread_wrapper(filename)
              #Read values of Clearence Normalized and date of examination into a return list
              date_of_examination = datetime.datetime.strptime(move_response_dataset.StudyDate,'%Y%m%d')
              date_list.append(date_of_examination)
              logger.info(f'Type of birthday: {type(birthday)} Type of date_of_examination:{type(date_of_examination)}')
              age_at_examination = (date_of_examination - birthday).days / 365
              age_list.append(age_at_examination)
              clearence_norm_list.append(float(move_response_dataset.normClear))

              history_dataset = Dataset()
              try: #fill dataset
                history_dataset.StudyDate = move_response_dataset.StudyDate
                history_dataset.clearance = move_response_dataset.clearance
                history_dataset.normClear = move_response_dataset.normClear
                history_dataset.ClearTest = move_response_dataset.ClearTest
                history_dataset.injTime   = move_response_dataset.injTime
              except AttributeError:
                logger.info(move_response_dataset)


              history_datasets.append(history_dataset)
              #Delete the file
              logger.info(f'Deleteing File: {filename}')
              os.remove(filename)
            except Exception as E:
              logger.warn(f'Error handling {accession_number} with {E}')
          elif move_status.Status == 0xFF00:
            pass      
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
  #Fill the dicom object:
  dicomlib.fill_dicom(dataset)
  
  #Return
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

  #End Helper Functions

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

  find_ae = pynetdicom.AE(ae_title=server_config.SERVER_AE_TITLE)
  move_ae = pynetdicom.AE(ae_title=server_config.SERVER_AE_TITLE)

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
      move_response = move_assoc.send_c_move(find_response_dataset, server_config.SERVER_AE_TITLE, query_model='S')
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

    #Finallize Association
    find_assoc.release()
    move_assoc.release()
  else:
    logger.error('Could not connect to pacs')
    #While unlikely a bug could be there
    if find_assoc.is_established:
      find_assoc.release()
    if move_assoc.is_established:
      move_assoc.release()

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


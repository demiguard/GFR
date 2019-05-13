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

def move_from_pacs(user, accession_number, patient_id = "", series_id = "", study_id = "", instance_id = ""):
  """


    Returns:
      None or Dataset
  """
  # # # Get file from pacs # # #
  #Create Dataset
  ds = Dataset()
  ds.PatientID = patient_id #0x00100020
  ds.SOPInstanceUID = instance_id #0x00080018
  ds.add_new(0x00080052, 'CS', 'STUDY') #Query level
  ds.StudyInstanceUID = study_id #0x0020000D 
  ds.SeriesInstanceUID = series_id #0x0020000E

  ae = AE(ae_title=server_config.SERVER_AE_TITLE)
  ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.2')
  assoc = ae.associate(user.config.pacs_ip, int(user.config.pacs_port), ae_title=user.config.pacs_calling)

  if assoc.is_established:
    successfull_move = False
    response = assoc.send_c_move(
      ds,
      server_config.SERVER_AE_TITLE,
      query_model='S'
      )
    for (status, identifier) in response:
      if status.Status == 0x0000:
        # We are successful
        logger.info('C-move successful')
        successfull_move = True
      if status.Status == 0xFF00:
        #We are not done, but shit have not broken down
        pass
      else:
        logger.warn('C-Move move opration failed with Status code:{0}'.format(hex(status.Status)))
    assoc.release()
  else:
    logger.warn('Move_from_pacs could not connect to pacs')
    return None

  file_src = server_config.SEARCH_DIR + accession_number + '.dcm'
  file_dst = server_config.SEARCH_DIR + user.hospital + '/' + accession_number + '.dcm'
  if successfull_move and os.path.exists(file_src):
    dirmanager.check_combined_and_create(server_config.SEARCH_DIR, user.hospital) #Ensure The correct file
    shutil.move(file_src, file_dst)
    dataset = dicomlib.dcmread_wrapper(file_dst)
    return examination_info.deserialize(dataset)    
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
  
  # Insert AccessionNumber into query file
  find_query = dicomlib.dcmread_wrapper(BASE_FIND_QUERY_PATH)
  find_query.AccessionNumber = rigs_nr
  find_query.save_as(BASE_FIND_QUERY_PATH)

  # Construct and execute command
  find_query = [
    server_config.FINDSCU,
    '-S',
    user.config.pacs_ip,
    user.config.pacs_port,
    '-aet',
    user.config.pacs_calling,
    '-aec',
    user.config.pacs_aet,
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
    user.config.pacs_ip,
    user.config.pacs_port,
    BASE_IMG_QUERY_PATH,
    '-aet',
    user.config.pacs_calling,
    '-aec',
    user.config.pacs_aet,
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
  # Update Pydicom with our tags
  DicomDictionary.update(server_config.new_dict_items)
  new_names_dirc = dict([(val[4], tag) for tag, val in server_config.new_dict_items.items()])
  keyword_dict.update(new_names_dirc)
  
  # Read after dictionary update
  try:
    obj = dicomlib.dcmread_wrapper('{0}/{1}.dcm'.format(resp_dir, rigs_nr))

  except FileNotFoundError:
    # Get object from DCM4CHEE/PACS Database
    obj = get_from_pacs(user, rigs_nr, resp_dir)

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
    user.config.pacs_calling,
    '-aec',
    user.config.pacs_aet,
    user.config.pacs_ip,
    user.config.pacs_port,
    obj_path
  ]
  
  out = execute_query(store_query)

  return (out != None)

def store_dicom_pacs(dicom_object, user, ensure_standart = True ):
  """
    Stores a dicom object in the user defined pacs (user.config)
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
  ae.add_requested_context('1.2.840.10008.5.1.4.1.1.7')
  assoc = ae.associate(
    user.config.pacs_ip,
    user.config.pact_port,
    ae_title=user.config.pacs_aet
  )

  if assoc.is_established:
    status = assoc.send_c_store(dicom_object, )
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
    Stores a Files 



    """
    logger.info('Recieved C-STORE')
    filename = '{0}.dcm'.format(
      dataset.AccessionNumber
    )
    
    fullpath = server_config.SEARCH_DIR + filename

    dicomlib.save_dicom(fullpath, dataset)

    return 0x0000

  def on_move(dataset, move_aet, context, info):
    """
      C-Move is unsupported by our Application as we do not have access to the list


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

  event_handlers = [
    (evt.EVT_ASYNC_OPS, log_event_handler),
    (evt.EVT_SOP_COMMON, sop_common_handler),
    (evt.EVT_SOP_EXTENDED, sop_extended_handler),
    (evt.EVT_USER_ID, log_event_handler), 
    # No Response
    (evt.EVT_ABORTED, log_event_handler),
    (evt.EVT_CONN_OPEN, log_event_handler),
    (evt.EVT_REQUESTED, log_event_handler),
  ]

  dirmanager.check_combined_and_create(server_config.SEARCH_DIR)

  server_ae = AE(ae_title=server_config.SERVER_AE_TITLE)
  server_ae.supported_contexts = StoragePresentationContexts
  server_ae.on_c_store = on_store
  server_ae.on_c_move = on_move

  server_instance = server_ae.start_server(('', 104), block=False, evt_handlers=event_handlers)

  return server_instance

def search_query_pacs(user, name="", cpr="", accession_number= "", date_from = "", date_to = ""):
  
  response_list = []
  #Construct Search Dataset
  search_dataset = dataset_creator.create_search_dataset(name, cpr, date_from, date_to, accession_number)

  #Construct AE
  ae = AE(ae_title=server_config.SERVER_AE_TITLE)
  ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.1')

  #Connect with AE
  assoc = ae.associate(user.config.pacs_ip, int(user.config.pacs_port), ae_title=user.config.pacs_aet)
  if assoc.is_established:
    #Make Search Request
    response = assoc.send_c_find(search_dataset, query_model='S')
    for (status, dataset) in response:
      if status.Status == 0xFF00:
        exam_obj = examination_info.deserialize(dataset)
        response_list.append(exam_obj)
      elif status.Status == 0x0000:
        #Operation successfull
        assoc.release()
      else:
        logger.info('Error, recieved status:{0}\n{1}'.format(hex(status.Status), status))
    assoc.release()
  else:
    logger.warn('Connection to pacs failed!')

  return response_list

  #Handle

def search_pacs(user, name="", cpr="", rigs_nr="", date_from="", date_to=""):
  """
  Searches PACS for basic examination/patient information

  Args:
    user: the currently signed in user
    name: name to search for
    cpr: cpr number to search for
    rigs_nr: rigs number to search for
    date_from: date to search from
    date_to: date to search until

  Returns:
    list of ExaminationInfo objects containing information about the search results.
    returns None if the command failed to execute.

  Remarks:
    Wildcards: the search parameters, i.e. the keyword args. to this function,
               can also be passed dicom wildcard, e.g. '*' for the name arg.
               to search for any name, or '20190101-' in date_from to search
               for any date from 2019-01-01 until the present day.

    There is no need to use the dcmwrapper function from dicomlib here, since 
    the search functionality doesn't rely on any private tags.
  """
  # Construct new query file - create dirs if necessary
  base_filename = "search_query"

  if not os.path.exists(server_config.SEARCH_DIR):
    os.mkdir(server_config.SEARCH_DIR)

  search_file_hash = random.getrandbits(128)

  curr_search_file = "{0}{1}{2}.dcm".format(
    server_config.SEARCH_DIR,
    base_filename,
    search_file_hash
  )

  curr_resp_dir = "{0}rsp{1}/".format(server_config.SEARCH_DIR, search_file_hash)

  shutil.copyfile(server_config.BASE_SEARCH_FILE, curr_search_file)
  os.mkdir(curr_resp_dir)

  # Fill out query file
  query_obj = pydicom.dcmread(curr_search_file)
  
  query_obj.PatientName = formatting.name_to_person_name(name)
  query_obj.PatientID = cpr
  query_obj.AccessionNumber = rigs_nr
  query_obj.StudyDate = "{0}-{1}".format(date_from, date_to)

  query_obj.save_as(curr_search_file)

  # Execute query
  search_query = [
    server_config.FINDSCU,
    "-S",
    "-aet",
    user.config.pacs_calling,
    "-aec",
    user.config.pacs_aet,
    user.config.pacs_ip,
    user.config.pacs_port,
    curr_search_file,
    '-X',
    '-od',
    curr_resp_dir
  ]

  execute_query(search_query)

  # Get responses
  ret = []

  for resp_file in glob.glob("{0}/*".format(curr_resp_dir)):
    resp_obj = pydicom.dcmread(resp_file)
    
    tmp_exam = ExaminationInfo()

    tmp_exam.name = formatting.format_name(resp_obj.PatientName)
    tmp_exam.cpr = formatting.format_cpr(resp_obj.PatientID)
    tmp_exam.rigs_nr = resp_obj.AccessionNumber
    tmp_exam.date = formatting.format_date(resp_obj.StudyDate)

    ret.append(tmp_exam)

  # Remove query dirs and files
  os.remove(curr_search_file)
  shutil.rmtree(curr_resp_dir)

  # Return
  return ret

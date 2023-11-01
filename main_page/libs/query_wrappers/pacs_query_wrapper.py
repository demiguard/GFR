import pydicom, pynetdicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict
from pynetdicom import AE, StoragePresentationContexts, evt
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind, StudyRootQueryRetrieveInformationModelMove
import os
import shutil
import glob
import datetime
import threading
import time
import json


from main_page import log_util
from main_page import models

from main_page.libs import ae_controller
from main_page.libs import dicomlib, dataset_creator
from main_page.libs import server_config
from main_page.libs import formatting

from main_page.libs.clearance_math import clearance_math
from main_page.libs.dirmanager import try_mkdir

logger = log_util.get_logger("")

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
  if 'move_assoc' and 'AE_title' in kwargs:
    move_assoc = kwargs['move_assoc']
    AE_title     = kwargs['AE_title']
  else:
    logger.info('config or move_assoc doesn\'t exsists')
    raise AttributeError("move_assoc and config is a required keyword")

  ae_controller.send_move(
    move_assoc,
    AE_title,
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
  if not config.pacs:
    return None, "Error: No PACS address set for configuration."

  #AE_title = models.ServerConfiguration.objects.get(id=1).AE_title
  AE_title = config.ris_calling

  pacs_find_ae = ae_controller.create_find_AE(AE_title)
  pacs_move_ae = ae_controller.create_move_AE(AE_title)

  pacs_find_assoc = ae_controller.establish_assoc(
    pacs_find_ae,
    config.pacs.ip,
    config.pacs.port,
    config.pacs.ae_title,
    logger
  )
  if not(pacs_find_assoc):
    return None, "Error"

  pacs_move_assoc = ae_controller.establish_assoc(
    pacs_move_ae,
    config.pacs.ip,
    config.pacs.port,
    config.pacs.ae_title,
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
    AE_title=AE_title)

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
  #AE_title = models.ServerConfiguration.objects.get(id=1).AE_title
  AE_title = user.department.config.ris_calling
  # Save the dicom file to be sent to PACS
  try_mkdir(server_config.PACS_QUEUE_DIR, mk_parents=True)
  store_file = f"{server_config.PACS_QUEUE_DIR}{accession_number}.dcm"

  dicomlib.save_dicom(store_file, dicom_object)

  if not user.department.config.pacs:
    return False, "Error: No PACS address in configuration."

  # Write file with connection configurations
  # hey hey hey, I present the newest programming invention:
  # MULTIPLE FUNCTIONAL ARGUMENTS, no more writing a file, and opening it up
  with open(f"{server_config.PACS_QUEUE_DIR}{accession_number}.json", "w") as fp:
    fp.write(json.dumps({
      "pacs_calling": AE_title,
      "pacs_ip":    user.department.config.storage.ip,
      "pacs_port":  user.department.config.storage.port,
      "pacs_aet":   user.department.config.storage.ae_title,
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
      logger.error(f"Failed to send study to PACS: {ds_file}, with parmeters: {conf['pacs_ip']} - {conf['pacs_port']} aet: {conf['pacs_aet']} aec: {conf['pacs_calling']}")
      time.sleep(wait_time)

  # Clean up or report if failed to send to PACS
  if is_sent:
    os.remove(ds_file)
    os.remove(conf_file)
  else:
    logger.error(f"Failed to send study to PACS: {ds_file}.")


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
      daemon=True,
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
      return_dataset.add_new(0x00000902, 'LO', 'Could not load retrieve Dataset')

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
      return return_dataset


  def sop_common_handler(event):
    logger.info(event)

  def sop_extended_handler(event):
    logger.info(event)

  def log_event_handler(event):
    logger.info(event)

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
  #End helper

  #AE_title = models.ServerConfiguration.objects.get(id=1).AE_title
  AE_title = config.ris_calling
  # Construct Search Dataset
  search_dataset = dataset_creator.create_search_dataset(
    name,
    cpr,
    date_from,
    date_to,
    accession_number
  )

  # Don't query if no PACS address
  if not config.pacs:
    logger.warning(f"Unable to execute search query. No PACS address in configuration: {config}.")
    return None

  # Establish association to PACS
  association = ae_controller.connect(
    config.pacs.ip,
    int(config.pacs.port),
    AE_title,
    config.pacs.ae_title,
    ae_controller.FINDStudyRootQueryRetrieveInformationModel
  )

  # Send find query and process successful responses
  response_list = [ ]

  try:
    ae_controller.send_find(
      association,
      search_dataset,
      process_incoming_dataset,
      logger=logger
    )
  except ValueError:
    logger.error(f"Failed to establish association to PACS with parameters:\npacs_ip: {config.pacs.ip}, pacs_port: {config.pacs.port}, pacs_calling: {AE_title}, pacs_aet: {config.pacs.ae_title}")
    return None

  association.release()

  logger.info(f'Returning search list of {len(response_list)}')

  return response_list


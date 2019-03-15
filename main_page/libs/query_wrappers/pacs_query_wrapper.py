import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict
import os
import sys
import shutil
import glob
import datetime
import calendar
import numpy
import pandas

from .. import dicomlib
from .. import server_config
from ..clearance_math import clearance_math
from .. import examination_info
from ..examination_info import ExaminationInfo
from .. import formatting
from .query_executer import execute_query


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
  rsp_paths = glob.glob(resp_path + 'rsp*.dcm') # list(filter(lambda x: 'rsp' in x, os.listdir(resp_path)))
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

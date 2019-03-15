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
from query_executer import execute_query


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

  # TODO: Update this to the first respons file from the findscu command is deleted immediately after use

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
  new_dict_items = {
    0x00231001 : ('LO', '1', 'GFR', '', 'GFR'), #Normal, Moderat Nedsat, Svært nedsat
    0x00231002 : ('LO', '1', 'GFR Version', '', 'GFRVersion'), #Version 1.
    0x00231010 : ('LO', '1', 'GFR Method', '', 'GFRMethod'),
    0x00231011 : ('LO', '1', 'Body Surface Method', '', 'BSAmethod'),
    0x00231012 : ('DS', '1', 'clearence', '', 'clearence'),
    0x00231014 : ('DS', '1', 'normalized clearence', '', 'normClear'),
    0x00231018 : ('DT', '1', 'Injection time', '', 'injTime'),     #Tags Added
    0x0023101A : ('DS', '1', 'Injection weight', '', 'injWeight'),
    0x0023101B : ('DS', '1', 'Vial weight before injection', '', 'injbefore'),
    0x0023101C : ('DS', '1', 'Vial weight after injection', '', 'injafter'),
    0x00231020 : ('SQ', '1-100', 'Clearence Tests', '', 'ClearTest'),
    0x00231021 : ('DT', '1', 'Sample Time', '', 'SampleTime'), #Sequence Items
    0x00231022 : ('DS', '1', 'Count Per Minuts', '', 'cpm'),
    0x00231024 : ('DS', '1', 'Standart Counts Per', '', 'stdcnt'),
    0x00231028 : ('DS', '1', 'Thining Factor', '', 'thiningfactor')
  }

  DicomDictionary.update(new_dict_items)
  new_names_dirc = dict([(val[4], tag) for tag, val in new_dict_items.items()])
  keyword_dict.update(new_names_dirc)
  
  # Read after dictionary update
  try:
    obj = dicomlib.dcmread_wrapper('{0}/{1}.dcm'.format(resp_dir, rigs_nr))
  except FileNotFoundError:
    # Get object from DCM4CHEE/PACS Database
    obj = get_from_pacs(user, rigs_nr, resp_dir)
  
  exam = ExaminationInfo()

  exam.rigs_nr = obj.AccessionNumber
  exam.cpr = formatting.format_cpr(obj.PatientID)
  exam.date = formatting.format_date(obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate)
  exam.name = formatting.format_name(obj.PatientName)

  # Depermine patient sex based on cpr nr. if not able to retreive it
  if 'PatientSex' in obj:
    exam.sex = obj.PatientSex
  else:
    exam.sex = clearance_math.calculate_age(exam.cpr)

  if 'PatientWeight' in obj:
    exam.weight = obj.PatientWeight
  
  if 'PatientSize' in obj:
    exam.height = obj.PatientSize
  
  if 'PatientAge' in obj:
    exam.age = obj.PatientAge
  else:
    exam.age = clearance_math.calculate_age(exam.cpr)



  try_get_exam_info('clearence', (0x0023,0x1012), no_callback)
  try_get_exam_info('clearence_N', (0x0023,0x1014), no_callback)
  try_get_exam_info('GFR', (0x0023,0x1001), no_callback)
  try_get_exam_info('inj_before', (0x0023,0x101B), no_callback)
  try_get_exam_info('inj_after', (0x0023,0x101C), no_callback)

  if 'ClearTest' in obj:
    if 'thiningfactor' in obj.ClearTest[0]:
      exam.thin_fact = obj.ClearTest[0].thiningfactor
    if 'stdcnt' in obj.ClearTest[0]:
      exam.std_cnt = obj.ClearTest[0].stdcnt

    sample_times = []
    tch99_cnt = []
    for test in obj.ClearTest:
      if 'SampleTime' in test:
        sample_times.append(datetime.datetime.strptime(test.SampleTime, '%Y%m%d%H%M'))
      if 'cpm' in test:
        if isinstance(test.cpm, bytes):
          tch99_cnt.append(test.cpm.decode())
        else:
          tch99_cnt.append(test.cpm)

    exam.sam_t = numpy.array(sample_times)
    exam.tch_cnt = numpy.array(tch99_cnt)

  if 'injTime' in obj:
    exam.inj_t = datetime.datetime.strptime(obj.injTime, '%Y%m%d%H%M')
    
  if 'PatientSize' in obj and 'PatientWeight' in obj:
    exam.BSA = clearance_math.surface_area(obj.PatientSize, obj.PatientWeight)

  if 'PixelData' in obj:
    exam.image = numpy.array(obj.pixel_array)

  if 'GFRMethod' in obj:
    exam.Method = obj.GFRMethod

  return exam


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

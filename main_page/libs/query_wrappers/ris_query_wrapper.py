import glob
import os
import datetime
import random
import shutil
import pydicom

from ... import models

from .. import dicomlib
from .. import server_config
from ..clearance_math import clearance_math
from .. import examination_info
from ..examination_info import ExaminationInfo
from .query_executer import execute_query


def parse_bookings(resp_dir):
  """
  Get dicom objects for all responses

  Args:
    resp_dir: path to directory containing dicom responses from findscu

  Returns:
    dict of dicom objects for all responses
  """
  ret = {}

  # Loop all responses
  for dcm_path in glob.glob('{0}/rsp*.dcm'.format(resp_dir)):
    ret[dcm_path] = dicomlib.dcmread_wrapper(dcm_path)

  return ret


def is_old_dcm_obj(obj_path):
  """
  Determines whether a dicom object is too old (i.e. it should be removed)

  Args:
    obj_path: path to the dicom obj to check

  Returns:
    True, the dicom object was to old and has been removed.
    False, the dicom object was NOT to old and still remains

  Remark:
    Only accepts valid dicom objects
  """
  obj = dicomlib.dcmread_wrapper(obj_path)
  
  exam = examination_info.deserialize(obj)

  # If more then 3 days old remove it
  procedure_date = datetime.datetime.strptime(exam.date, '%d/%m-%Y')

  now = datetime.datetime.now()
  time_diff = now - procedure_date
  days_diff = time_diff.days
  
  if days_diff >= server_config.DAYS_THRESHOLD:
    os.remove(obj_path)
    return True

  return False


def get_all(user):
  """
  Get registed examinations from a specific hospital, using a user

  Args:
    user: the currently logged in user object

  Returns:
    Ordered list, based on names, of ExaminationInfo instances containing infomation 
    about examinations registed at the specified hospital.
  """
  # Create query file
  base_query_file = server_config.BASE_RIGS_QUERY

  query_file = '{0}_{1}.dcm'.format(
    base_query_file.split('.')[0],
    random.getrandbits(128)
  )

  shutil.copy(base_query_file, query_file)

  qf_obj = pydicom.dcmread(query_file)
  qf_obj.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = user.config.rigs_calling
  qf_obj.save_as(query_file)

  base_resp_dir = server_config.FIND_RESPONS_DIR
  resp_dir = '{0}{1}/'.format(base_resp_dir, user.hospital)

  if not os.path.exists(base_resp_dir):
    os.mkdir(base_resp_dir)

  if not os.path.exists(resp_dir):
    os.mkdir(resp_dir)

  # Construct query and execute
  query_arr = [
    server_config.FINDSCU,
    '-aet', # Set calling AET
    user.config.rigs_calling,
    '-aec', # Set AET to call
    user.config.rigs_aet,
    user.config.rigs_ip,
    user.config.rigs_port,
    query_file,
    '-X',  # Extract responses
    '-od', # Output dir to extract into
    resp_dir
  ]

  exe_out = execute_query(query_arr)

  if exe_out != '':
    pass # TODO: Error handling for failed findscu execution

  # Remove the query file after execution
  os.remove(query_file)

  dcm_objs = parse_bookings(resp_dir)
  ret = []

  # Add previous examinations to return list
  for obj_path in glob.glob('{0}REGH*.dcm'.format(resp_dir)):
    if not is_old_dcm_obj(obj_path):
      obj = dicomlib.dcmread_wrapper(obj_path)
      ret.append(examination_info.deserialize(obj))

  # Add new examinations to return list
  accepted_procedures = user.config.accepted_procedures.split('^')

  for obj_path, obj in dcm_objs.items():
    if obj.RequestedProcedureDescription in accepted_procedures:
      # Save to file if not already retreived
      if not os.path.exists('{0}{1}.dcm'.format(resp_dir, obj.AccessionNumber)):
        exam = examination_info.deserialize(obj)
        obj.save_as('{0}{1}.dcm'.format(resp_dir, obj.AccessionNumber))
        ret.append(exam)

    # Remove the response file
    os.remove(obj_path)
  
  # Filter out examinations previously sent to PACS
  def sent_to_pacs(ex):
    return not models.HandledExaminations.objects.filter(rigs_nr=ex.rigs_nr).exists()
  
  ret = list(filter(sent_to_pacs, ret))
  
  return list(sorted(ret, key=lambda x: x.name))

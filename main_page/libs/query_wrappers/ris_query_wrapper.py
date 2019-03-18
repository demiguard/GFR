import glob
import os

from .. import dicomlib
from .. import server_config
from ..clearance_math import clearance_math
from .. import examination_info
from ..examination_info import ExaminationInfo
from .. import formatting
from .query_executer import execute_query


def parse_bookings(resp_dir):
  """
  Get dicom objects for all responses

  Args:
    resp_dir: path to directory containing dicom responses from findscu

  Returns:
    List of dicom objects for all responses
  """
  ret = {}

  # Loop all responses
  for dcm_path in glob.glob('{0}/rsp*.dcm'.format(resp_dir)):
    ret[dcm_path] = dicomlib.dcmread_wrapper(dcm_path)

  return ret


def get_all(user):
  """
  Get registed patients from a specific hospital, using a user

  Args:
    user: the currently logged in user object

  Returns:
    Ordered list, based on names, of ExaminationInfo instances containing infomation 
    about patients registed at the specified hospital.
  """  
  edta_obj = dicomlib.dcmread_wrapper('main_page/libs/edta_query.dcm')

  # Create dcm filter
  edta_obj.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = user.config.rigs_calling

  query_file = 'main_page/libs/edta_query_{0}.dcm'.format(user.config.rigs_calling)
  edta_obj.save_as(query_file)

  base_resp_dir = server_config.FIND_RESPONS_DIR
  DICOM_dirc = '{0}{1}'.format(base_resp_dir, user.hospital)

  if not os.path.exists(base_resp_dir):
    os.mkdir(base_resp_dir)

  if not os.path.exists(DICOM_dirc):
    os.mkdir(DICOM_dirc)

  resp_dir = '{0}'.format(DICOM_dirc)

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

  # Extract needed info from dcm objects (w/ formatting)
  ret = []
  accepted_procedures = user.config.accepted_procedures.split('^')

  for key, obj in dcm_objs.items():
    if obj.RequestedProcedureDescription in accepted_procedures:
      exam = ExaminationInfo()
      
      exam.rigs_nr = obj.AccessionNumber
      exam.cpr = formatting.format_cpr(obj.PatientID)
      exam.date = formatting.format_date(obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate)
      exam.name = formatting.format_name(obj.PatientName)

      exam.rigs_nr = obj.AccessionNumber
      exam.cpr = formatting.format_cpr(obj.PatientID)
      exam.date = formatting.format_date(obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate)
      exam.name = formatting.format_name(obj.PatientName)

      ret.append(exam)
      
      # Save to dcm file with rigs nr. as  corresponding rsp file
      if not os.path.exists('{0}/{1}.dcm'.format(resp_dir, obj.AccessionNumber)):
        obj.save_as('{0}/{1}.dcm'.format(resp_dir, obj.AccessionNumber))

    os.remove(key)
  
  return sorted(ret, key=lambda x: x.name)

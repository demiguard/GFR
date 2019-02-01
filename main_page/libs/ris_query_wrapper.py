from subprocess import check_output
from .clearance_math import clearance_math

import pydicom
import os
import shutil
import glob
import datetime
import calendar
import numpy
import pandas

"""
findscu -S 127.0.0.1 11112 -aet RH_EDTA -aec TEST_DCM4CHEE -k 0008,0050="REGH13630168" -k 0008,0052="STUDY" -k 0010,0020 -k 0020,000D -X
getscu -P 127.0.0.1 11112 -k 0008,0052="STUDY" -k 0010,0020="1909640853" -k 0020,000D="1.3.51.0.1.1.10.143.20.159.13630168.6612553" -aec TEST_DCM4CHEE -aet RH_EDTA -od .
"""

class ExaminationInfo():
  def __init__(self):
    self.info = {
      'ris_nr' :'',
      'name'   :'',
      'cpr'    :'',
      'age'    :'',
      'date'   :'',
      'sex'    :'',
      'height' :0.0,
      'weight' :0.0,
      'BSA'    :'',
      'GFR'    :'',
      'GFR_N'  :'',
      'Method' :'',
      'inj_t'  : datetime.datetime(2000,1,1,0,0),
      'sam_t'  : numpy.array([]), #Datetime list
      'tch_cnt': numpy.array([]), #list of technisium count
      'dosis'  : 0,
      'image'  : numpy.array([]) #pixeldata
    }

# Class done

# TODO: Move these to config file
RIGS_AET = "VIMCM"
RIGS_IP = "10.143.128.247"
RIGS_PORT = "3320"

# NOTE: This is currently setup for storage on the local test server 
# (ONLY change this to the actual PACS server when in production)
PACS_AET = 'TEST_DCM4CHEE'
PACS_IP = '193.3.238.103'
PACS_PORT = '11112' # Or 11112 if no port-forwarding

CALLING_AET = "RH_EDTA"

DUMP2DCM = "dump2dcm"
FINDSCU = "findscu"
STORESCU = 'storescu'



def execute_query(cmd):
  """Executes a query and 
  
  Args:
    cmd: command query to execute

  Return:
    Output from the ran command

  Remark: 
    This function should be extended to handle potential errors 
    in the execution of the query command
  """
  return check_output(cmd)

def store_dicom(dicom_obj_path, tags, values, value_reps):
  """
  Stores value in the tags of the dicom
  Value Rep is 

  Args:
    dicom_obj: The object to store

  Remarks
    Using this function it's only posible to store sequences of a single type.
    So for instance it can store a sequence of sequences of dates, but not a
    a sequence containing a sequence of dates and floats
  """
  ds = pydicom.dcmread(dicom_obj_path)

  for tag, val, val_rep in zip(tags, values, value_reps):
    ds.add_new(tag, val_rep, val)
  
  ds.save_as(dicom_obj_path)

def store_private_tag(dicom_obj_path, tag, tag_block, tag_group, value, value_rep):
  """
  For a tag tttt, tag_block bb and tag_group gg, value_rep VR. 
  Store the value at the tag [0xtttt,0xbbgg] with VR and create
  the value: VR [0xtttt,0x00bb] with 'LO' 

  Args:
    dicom_obj_path: Path to dicom object 
    tag           : An uneven hex on the form 0xgggg 
    tag_block     : A hex larger than 0x10 but less than 0xFF
    tag_group     : A hex less than 0xFF

  returns: 0 on success


  """
  if tag % 2 == 1     : return 1
  if tag >  0xFFFF    : return 1
  if tag <  0x0010    : return 1
  if tag_block > 0xFF : return 1
  if tag_block < 0x10 : return 1
  if tag_group > 0xFF : return 1

  ds = pydicom.dcmread(dicom_obj_path)
  
  for t, t_block, t_group, v, vr in zip(tag, tag_block, value, value_rep):
    ds.add_new((t, t_block), 'LO', vr)
    
    save_tag = hex((tag_block << 8) + tag_group)

    ds.add_new((t, save_tag), vr, v)

  return 0

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
    ret[dcm_path] = pydicom.dcmread(dcm_path)

  return ret

def format_name(name):
  """
  Formats a name to the format: Firstname Middlename Lastname
  """
  name = str(name)
  name_split = name.split('^')
  
  fst = name_split[0]
  
  del name_split[0]
  name_split.append(fst)

  name_split = list(filter(None, name_split))

  return ' '.join(name_split)

def format_cpr(cpr):
  """
  Formats a cpr nr. to the format: XXXXXX-XXXX
  """
  cpr = str(cpr)
  return cpr[:6] + '-' + cpr[6:]

def format_date(date):
  """
  Formats a date to the format: DD/MM-YYYY
  """
  date = str(date)
  year = date[:4]
  month = date[4:6]
  day = date[6:8]
  return '{0}/{1}-{2}'.format(day, month, year)


def get_examination(rigs_nr, resp_dir):
  """
  Retreive examination information based on a specified RIGS nr.

  Args:
    rigs_nr: RIGS nr of examination

  Returns:
    ExaminationInfo instance containing examination information for the specified
    RIGS nr.
  """
  # TODO: Add error handling for invalid filepath
  # Throw the specific RIGS nr input a dicom obj and use it to query for the examination
  obj = pydicom.dcmread('{0}/{1}.dcm'.format(resp_dir, rigs_nr))

  examination_info = ExaminationInfo()
  
  for key in examination_info.info:
    # TODO: Figure out smart function for passing info
    #
    pass

  # Remark: no need to format, since cached dcm objects are alread formatted.
  examination_info.info['ris_ nr'] = obj.AccessionNumber
  examination_info.info['cpr'] = format_cpr(obj.PatientID)
  examination_info.info['date'] = format_date(obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate)
  examination_info.info['name'] = format_name(obj.PatientName)

  # Try to read optional patient/examination attributes from previous examinations
  def try_get_exam_info(key, tags, err_callback, *args, **kwargs):
    try:
      examination_info.info[key] = obj[tags[0], tags[1]].value
    except KeyError:
      examination_info.info[key] = err_callback(*args, **kwargs)

  def no_callback(*args, **kwargs):
    pass

  # Depermine patient sex based on cpr nr. if not able to retreive it
  try_get_exam_info('sex', (0x0010, 0x0040), clearance_math.calculate_sex, examination_info.info['cpr'])
  try_get_exam_info('weight', (0x0010, 0x1030), no_callback)
  try_get_exam_info('height', (0x0010, 0x1020), no_callback)
  try_get_exam_info('age', (0x0010, 0x1010), clearance_math.calculate_age, examination_info.info['cpr'])
  try_get_exam_info('BSA', (0x0000,0x0000) , no_callback)
  try_get_exam_info('GFR', (0x0000,0x0000), no_callback)
  try_get_exam_info('GFR_N', (0x0000,0x0000), no_callback)

  if 'PixelData' in obj:
    examination_info.info['image'] = numpy.array(obj.pixel_array)

  return examination_info

def get_all(hosp_aet):
  """
  Get registed patients from a specific hospital (by AET)

  Args:
    hosp_aet: AET corresponding to the hospital

  Returns:
    Ordered list, based on names, of ExaminationInfo instances containing infomation 
    about patients registed at the specified hospital.

  Example:
    hosp_aet='RH_EDTA' is Rigshospitalet
  """
  edta_obj = pydicom.dcmread('main_page/libs/edta_query.dcm')

  # Create dcm filter
  edta_obj.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = hosp_aet

  # Date filtering (removed)
  #curr_date = datetime.datetime.today().strftime('%Y%m%d')
  #edta_obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate = curr_date

  query_file = 'main_page/libs/edta_query_{0}'.format(hosp_aet)
  edta_obj.save_as(query_file)

  resp_dir = './tmp'
  try:
    os.mkdir(resp_dir)
  except FileExistsError:
    pass

  # Construct query and execute
  query_arr = [
    FINDSCU, 
    '-aet', # Set calling AET
    CALLING_AET,
    '-aec', # Set AET to call
    RIGS_AET,
    RIGS_IP,
    RIGS_PORT,
    query_file,
    '-X',  # Extract responses
    '-od', # Output dir to extract into
    resp_dir
  ]
  
  exe_out = execute_query(query_arr)
  if exe_out != '':
    pass # TODO: Error handling for failed findscu execution

  dcm_objs = parse_bookings(resp_dir)

  # Extract needed info from dcm objects (w/ formatting)
  ret = []
  accepted_procedures = [
    'Clearance Fler-blodprøve',
    'Clearance blodprøve 2. gang',
    'GFR, Cr-51-EDTA, one sampel',
  ]

  for key, obj in dcm_objs.items():
    if obj.RequestedProcedureDescription in accepted_procedures:
      examination_info = ExaminationInfo()
      
      examination_info.risnr = obj.AccessionNumber
      examination_info.cpr = format_cpr(obj.PatientID)
      examination_info.date = format_date(obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate)
      examination_info.name = format_name(obj.PatientName)

      ret.append(examination_info)

      # Save to dcm file with rigs nr. as  corresponding rsp file
      obj.save_as('{0}/{1}.dcm'.format(resp_dir, obj.AccessionNumber))
      os.remove(key)
  
  return sorted(ret, key=lambda x: x.name)

def check_cpr(cpr):  
  """
  Checks whether a given cpr number, as a string, is valid

  Args:
    cpr: cpr number to check

  Returns:
    None if valid cpr number, otherwise a string containing an error message
  """
  # Validate length and position of '-' char
  if len(cpr) == 10: # No '-' char
    pass
  elif len(cpr) == 11: # Cpr string contains '-' char
    if cpr[6] == '-':
      cpr = cpr.replace('-', '')
  else: 
    return "Incorrect CPR nr."

  # Check if digits and validate checksum
  if cpr.isdigit():
    cpr_int_arr = [int(i) for i in cpr]
    control_arr = [4,3,2,7,6,5,4,3,2,1]
    p_cpr = pandas.Series(cpr_int_arr)
    p_con = pandas.Series(control_arr)
  
    if (p_cpr * p_con).sum() % 11 == 0:
      return None

  return "Incorrect CPR nr."

def check_name(name):
  if name == '':
    return "No name given"
  
  if ' ' in name:
    return None

  return "No first or lastname given"

def check_date(date):
  """
  Checks whether a given study date is valid

  Args:
    date: study date to check

  Returns
    None if valid, otherwise returns a string containing an error message
  """
  if date.count('-') == 2:
    date = date.replace('-', '')

    if len(date) == 8:
      if date.isdigit():
        # Extract and validate specifics
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:])

        if month > 0 and month < 13:
          days_in_month = calendar.monthrange(year, month)[1] + 1

          if day > 0 and day < days_in_month:
            return None
          else:
            return "Invalid day in study date"
        else:
          return "Invalid month in study date"
      else:
        return "Invalid study date, contains none digit characters"
    else:
      return "Invalid study date, check format"

  return "Invalid study date, check format"

def check_ris_nr(ris_nr):
  """
  Checs if a given RIGS nr is valid

  Args:
    ris_nr: RIGS nr to check

  Returns:
    None if valid RIGS nr, otherwise returns a string containing an error message
  """
  if 'REGH' in ris_nr:
    return None

  return "Invalid RIGS nr, check format"

def is_valid_study(cpr, name, study_date, ris_nr):
  """
  Checks whether given study information is vaild.

  Args:
    cpr: cpr nr of patient
    name: name of patient
    study_date: date of the study
    ris_nr: RIGS number of the study

  Returns:
    tuple of the type (bool, string), if the study is valid then bool is True and
    string is None.
    Otherwise if the study is invalid bool is False and string contains an error
    message describing the all points where the study is invalid.
  """
  error_strings = []
  
  # Validate every input
  error_strings.append(check_cpr(cpr))
  error_strings.append(check_name(name))
  error_strings.append(check_date(study_date))
  error_strings.append(check_ris_nr(ris_nr))

  # Filter out None values
  error_strings = list(filter(lambda x: x, error_strings))

  return (len(error_strings) == 0, error_strings)

def store_study(ris_nr, resp_dir):
  """
  Stores a given study in the RIGS database

  Args:
    ris_nr: RIGS number of the study
    resp_dir: 

  Remark:
    Validation of the study is expected, before storing it
  """
  # Construct dicom obj to store
  obj_path = ""

  # Construct query and store
  store_query = [
    STORESCU,
    '-aet',
    CALLING_AET,
    '-aec',
    PACS_AET,
    PACS_IP,
    PACS_PORT,
    obj_path
  ]
  
  # TODO: Handle errors in the case of execution failure
  out = execute_query(store_query)

from subprocess import check_output, CalledProcessError
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

try:
  from ..clearance_math import clearance_math
except ImportError:
  # Allow relative import beyond upper top-level when running test script
  sys.path.append('../clearance_math')
  import clearance_math

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

# TODO: Change these to absolute paths when deploying, to avoid alias attacks
DUMP2DCM = "dump2dcm"
FINDSCU = "findscu"
STORESCU = 'storescu'
GETSCU = 'getscu'


def execute_query(cmd):
  """
  Executes a query comamnd
  
  Args:
    cmd: command query to execute

  Return:
    Output from the ran command, None if command returned non zero exit-code
  """  
  try:
    return check_output(cmd)
  except (CalledProcessError, FileNotFoundError):
    return None

def store_dicom(dicom_obj_path,
    height            = None,
    weight            = None,
    gfr               = None,
    gfr_type          = None,
    injection_time    = None,
    injection_weight  = None,
    injection_before  = None,
    injection_after   = None,
    bsa_method        = None,
    clearence         = None,
    clearence_norm    = None,
    sample_seq        = []
  ):
  """
  Saves information in dicom object, overwriting previous data, with no checks

  Args:
    dicom_obj_path  : string, path to the object where you wish information to stored

  Optional Args:
    height          : float, Height of patient wished to be stored
    weight          : float, Weight of patient wished to be stored
    gfr             : string, either 'Normal', 'Moderat Nedsat', 'Nedsat', 'Stærkt nedsat' 
    gfr_type        : string, Method used to calculate GFR
    injection_time  : string on format 'YYYYMMDDHHMM', Describing when a sample was injected
    injection_weight: float, Weight of injection
    injection_before: float, Weight of Vial Before injection
    injection_after : float, Weight of Vial After Injection
    bsa_method      : string, Method used to calculate Body Surface area
    clearence       : float, Clearence Value
    clearence_norm  : float, Clearence Value Normalized to 1.73m²
    sample_seq      : list of lists where every list is on the format: 
      *List_elem_1  : string on format 'YYYYMMDDHHMM', describing sample taken time
      *List_elem_2  : float, cpm of sample
      *List_elem_3  : float, stdcnt of the sample
      *List_elem_4  : float, Thining Factor of Sample. In most sane cases these are the same throught the list

  Remarks
    It's only possible to store the predefined args with this function
  """
  ds = pydicom.dcmread(dicom_obj_path)
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

  ds.add_new((0x00230010), 'LO', 'Clearence - Denmark - Region Hovedstaden')

  if height:
    ds.PatientSize = height

  if weight:
    ds.PatientWeight = weight

  if gfr:
    ds.GFR = gfr
    ds.GFRVersion = 'Version 1.0'

  if gfr_type:
    ds.GFRMethod = gfr_type

  if injection_time:
    ds.injTime = injection_time

  if injection_weight:
    ds.injWeight = injection_weight
  
  if injection_before:
    ds.injbefore = injection_before
  
  if injection_after:
    ds.injafter = injection_after

  if bsa_method:
    ds.BSAmethod = bsa_method

  if clearence:
    ds.clearance = clearence 

  if clearence_norm:
    ds.normClear = clearence_norm

  if sample_seq:
    seq = Sequence([])
    #Add Information About the Sample
    for sample in sample_seq:
      seq_elem = Dataset()
      seq_elem.SampleTime     = sample[0]
      seq_elem.cpm            = sample[1]
      seq_elem.stdcnt         = sample[2]
      seq_elem.thiningfactor = sample[3]

      seq.append(seq_elem)
    ds.ClearTest = seq

  ds.save_as(dicom_obj_path)

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

def get_from_pacs(rigs_nr, cache_dir, resp_path="./rsp/"):
  """
  Retreives an examination from a dicom database (DCM4CHEE/PACS)

  Args:
    rigs_nr: rigs number of patient to retreive
    cache_dir: directory for cached dicom objects

  Returns:
    Dicom object for the retreived patient, otherwise None

  Remarks:
    The below lines provides commandline examples for manually executing the queries:
    findscu -S 127.0.0.1 11112 -aet RH_EDTA -aec TEST_DCM4CHEE -k 0008,0050="REGH13630168" -k 0008,0052="STUDY" -k 0010,0020 -k 0020,000D -X
    getscu -P 127.0.0.1 11112 -k 0008,0052="STUDY" -k 0010,0020="1909640853" -k 0020,000D="1.3.51.0.1.1.10.143.20.159.13630168.6612553" -aec TEST_DCM4CHEE -aet RH_EDTA -od .
  """

  # TODO: Update this to the first respons file from the findscu command is deleted immediately after use

  BASE_FIND_QUERY_PATH = resp_path + "base_find_query.dcm"
  BASE_IMG_QUERY_PATH = resp_path + "base_get_image.dcm"
  
  # Insert AccessionNumber into query file
  find_query = pydicom.dcmread(BASE_FIND_QUERY_PATH)
  find_query.AccessionNumber = rigs_nr
  find_query.save_as(BASE_FIND_QUERY_PATH)

  # Construct and execute command
  find_query = [
    FINDSCU,
    '-S',
    PACS_IP,
    PACS_PORT,
    '-aet',
    CALLING_AET,
    '-aec',
    PACS_AET,
    BASE_FIND_QUERY_PATH,
    '-X',
    '-od',
    resp_path
  ]

  # TODO: Add error handling of failed queries (Update execute_query first to return exit-code)
  if not execute_query(find_query):
    return None

  # Use first resp
  rsp_paths = list(filter(lambda x: 'rsp' in x, os.listdir(resp_path)))
  if len(rsp_paths) != 0:
    rsp_path = resp_path + rsp_paths[0]
  else:
    return None

  # Extract Patient ID and Study Instance UID from respons
  patient_rsp = pydicom.dcmread(rsp_path)
  patient_id = patient_rsp.PatientID
  si_uid = patient_rsp.StudyInstanceUID

  os.remove(rsp_path)

  # Insert patient id and study instance uid into image query file
  img_query = pydicom.dcmread(BASE_IMG_QUERY_PATH)
  img_query.PatientID = patient_id
  img_query.StudyInstanceUID = si_uid
  img_query.save_as(BASE_IMG_QUERY_PATH)

  # Construct and execute image query
  img_query = [
    GETSCU,
    '-P',
    PACS_IP,
    PACS_PORT,
    BASE_IMG_QUERY_PATH,
    '-aet',
    CALLING_AET,
    '-aec',
    PACS_AET,
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

  obj = pydicom.dcmread(cache_path)
  return obj


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
  try:
    obj = pydicom.dcmread('{0}/{1}.dcm'.format(resp_dir, rigs_nr))
  except FileNotFoundError:
    # Get object from DCM4CHEE/PACS Database
    obj = get_from_pacs(rigs_nr, resp_dir)

  examination_info = ExaminationInfo()

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

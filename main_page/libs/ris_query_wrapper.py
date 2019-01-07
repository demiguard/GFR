from subprocess import check_output
import pydicom
import os
import shutil
import glob
import datetime

class ExaminationInfo():
  def __init__(self):
    self.risnr = ''
    self.name = ''
    self.cpr = ''
    self.date = ''
    self.sex = ''
    self.height = ''
    self.weight = ''
    self.age = ''

# TODO: Move these to config file
RIGS_AET = "VIMCM"
RIGS_IP = "10.143.128.247"
RIGS_PORT = "3320"

CALLING_AET = "RH_EDTA"

FINDSCU = "findscu"
DUMP2DCM = "dump2dcm"

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

def calculate_sex(cprnr):
  """
  Determine wheter the patient is male or female
  """
  if int(cprnr[-1]) % 2 == 0:
    return 'Dame'
  else:
    return 'Mand'

def calculate_age(cprnr):
  """
  Determine the age of a patient
  """
  year_of_birth = int(cprnr[4:6])
  month_of_birth = int(cprnr[2:4])
  day_of_birth = int(cprnr[0:2])
  
  current_time = datetime.datetime.now()
  
  # Check year (assume higher likelihood of kids, than people over 100)
  if year_of_birth < current_time.year - 2000:
    by_year = current_time.year - 2000 - year_of_birth
  else: 
    by_year = current_time.year - 1900 - year_of_birth

  # Check month and day
  if month_of_birth <= current_time.month:
    if day_of_birth <= current_time.day:
      by_year += 1

  return by_year

def get_examination(rigs_nr, resp_dir):
  """
  Retreive examination information based on a specified RIGS nr.

  Args:
    rigs_nr: RIGS nr of examination

  Returns:
    ExaminationInfo instance containing examination information for the specified
    RIGS nr.
  """
  obj = pydicom.dcmread('{0}/{1}.dcm'.format(resp_dir, rigs_nr))

  examination_info = ExaminationInfo()
  
  # Remark: no need to format, since cached dcm objects are alread formatted.
  examination_info.risnr = obj.AccessionNumber
  examination_info.cpr = format_cpr(obj.PatientID)
  examination_info.date = format_date(obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate)
  examination_info.name = format_name(obj.PatientName)

  # Try to read optional patient/examination attributes from previous examinations
  try:
    examination_info.sex = obj[0x0010, 0x0040]
  except KeyError:
    # Depermine patient sex based on cpr nr.
    examination_info.sex = calculate_sex(examination_info.cpr)

  try:
    examination_info.weight = obj[0x0010, 0x0030]
  except KeyError:
    pass

  try:
    examination_info.height = obj[0x0010, 0x0020]
  except KeyError:
    pass

  try:
    examination_info.age = obj[0x0010, 0x1010]
  except KeyError:
    examination_info.age = calculate_age(examination_info.cpr)

  print(examination_info.age)

  # Custom tags
  # try:
  #   examination_info.factor = obj[, ]
  # except KeyError:
  #   pass
    
  # try:
  #   examination_info.batch = obj[, ]
  # except KeyError:
  #   pass

  # try:
  #   examination_info.std_count = obj[, ]
  # except KeyError:
  #   pass
  
  # try:
  #   examination_info.vial = obj[, ]
  # except KeyError:
  #   pass

  # try:
  #   examination_info.vial_before = obj[, ]
  # except KeyError:
  #   pass

  # try:
  #   examination_info.vial_after = obj[, ]
  # except KeyError:
  #   pass

  # try:
  #   examination_info.injection_time = obj[, ]
  # except KeyError:
  #   pass

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

  query_file = 'main_page/libs/edta_query_{0}.dcm'.format(hosp_aet)
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
    print(key)
    if obj.RequestedProcedureDescription in accepted_procedures:
      examination_info = ExaminationInfo()
      
      examination_info.risnr = obj.AccessionNumber
      examination_info.cpr = format_cpr(obj.PatientID)
      examination_info.date = format_date(obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate)
      examination_info.name = format_name(obj.PatientName)

      ret.append(examination_info)

      # Save to dcm file with rigs nr. as filename, and remove corresponding rsp file
      obj.save_as('{0}/{1}.dcm'.format(resp_dir, obj.AccessionNumber))
      os.remove(key)

  return sorted(ret, key=lambda x: x.name)

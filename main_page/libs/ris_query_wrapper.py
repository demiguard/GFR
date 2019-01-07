from subprocess import check_output
import pydicom
import os
import shutil
import glob
import datetime
import calendar

class ExaminationInfo():
  def __init__(self):
    # TODO: Make this a directory so we can easily create a function for the try-catch when retreiving info
    # self.info = {
    #   'risnr': ''
    # }

    self.risnr = ''
    self.name = ''
    self.cpr = ''
    self.date = ''
    self.sex = ''
    self.height = ''
    self.weight = ''
    self.age = ''
    self.GFR = ''
    self.GFR_normalized = ''
    self.image = ''   #Path image
    

# Class done    

# TODO: Move these to config file
RIGS_AET = "VIMCM"
RIGS_IP = "10.143.128.247"
RIGS_PORT = "3320"

# NOTE: This is currently setup for storage on the local test server 
# (ONLY change this to the actual PACS server when in production)
PACS_AET = 'TEST_DCM4CHEE'
PACS_IP = 'localhost'
PACS_PORT = '104' # Or 11112 if no port-forwarding

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
  # TODO: Add error handling for invalid filepath
  # Throw the specific RIGS nr input a dicom obj and use it to query for the examination
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

def check_cpr(cpr):  
  """
  Checks whether a given cpr number, as a string, is valid

  Args:
    cpr: cpr number to check

  Returns:
    None if valid cpr number, otherwise a string containing an error message
  """
  if len(cpr) == 10: # No '-' char
    if cpr.isdigit():
      # Extract birthday
      byear = cpr[0:2]
      bmonth = cpr[2:4]
      bday = cpr[4:6]
      control_num = cpr[6:]

      # TODO: Perform checking based on official CPR protocol: https://www.cpr.dk/media/17534/personnummeret-i-cpr.pdf

      return None
  elif len(cpr) == 11: # Cpr string contains '-' char
    if cpr[6] == '-':
      cpr = cpr.replace('-', '')

      if cpr.isdigit():
        # TODO: Perform further checking, see above todo.

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

  return (len(error_strings) == 0, '\n'.join(error_strings))

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

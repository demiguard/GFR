import calendar
import pandas
import re
import logging
from datetime import datetime

from typing import Union

logger = logging.getLogger()

def person_name_to_name(name: str) -> str:
  """
  Formats dicom person names to names of form: Firstname [Middlenames] Lastnames

  Args:
    name: dicom person name

  Returns:
    the normally formatted name

  Remark:
    Specification for person names: http://dicom.nema.org/dicom/2013/output/chtml/part05/sect_6.2.html
    Examples at: http://dicom.nema.org/dicom/2013/output/chtml/part05/sect_6.2.html#sect_6.2.1.1
  """
  if '*' in name:
    raise ValueError(f"name: '{name}', contains a wildcard character: '*'")

  EXPECTED_LENGTH = 5
  FIRST_SUFFIX = 3
  SECOND_SUFFIX = 4
  FIRST_NAME = 1
  MIDDLE_NAME = 2
  LAST_NAME = 0

  name_split = name.split('^')

  # Append empty str, to avoid IndexErrors  
  for _ in range(len(name_split), EXPECTED_LENGTH):
    name_split.append('')

  if name_split[SECOND_SUFFIX]:
    ret = f"{name_split[FIRST_SUFFIX]} {name_split[FIRST_NAME]} {name_split[MIDDLE_NAME]} {name_split[LAST_NAME]}, {name_split[SECOND_SUFFIX]}"
  else:
    ret = f"{name_split[FIRST_SUFFIX]} {name_split[FIRST_NAME]} {name_split[MIDDLE_NAME]} {name_split[LAST_NAME]}"

  return ret.strip().replace('  ', ' ')


def format_cpr(cpr: str) -> str:
  """
  Formats a cpr nr. to the format: XXXXXX-XXXX

  Args:
    cpr: cpr number in string representation

  Remark:
    If the cpr string contains non-numeric characters the string is assumed
    correctly formatted 

  Raises:
    ValueError: if the incomming cpr number contains an invalid number of dashes 
  """
  # Assumed that if cpr contains characters from a to z, it correctly formatted,
  # e.g. for Icelandic cpr numbers
  if re.search(r"[a-zA-Z]", cpr):
    return cpr

  if not re.search(r"^[a-zA-Z0-9\-]+$", cpr):
    raise ValueError("cpr number contain illegal characters")

  # Optional dash at 6'th index check
  DASH_CNT = 1
  DASH_IDX = 6
  
  dash_indicies = [match.start(0) for match in re.finditer(r"-", cpr)]
  dash_idx_len = len(dash_indicies)

  if dash_idx_len == DASH_CNT:
    if dash_indicies[0] == DASH_IDX:
      return cpr
    else:
      raise ValueError(f"cpr: '{cpr}', contains dash at index: {dash_indicies[0]}, expected: {DASH_IDX}")
  elif dash_idx_len > DASH_CNT:
    raise ValueError(f"cpr: '{cpr}', contains more than one dash")

  return cpr[:DASH_IDX] + '-' + cpr[DASH_IDX:]


def format_date(date: str) -> str:
  """
  Formats a date string of form YYYYMMDD to DD/MM-YYYY

  Args:
    date: string representing the date

  Returns:
    Date string in DD/MM-YYYY format
  """
  date = datetime.strptime(date, "%Y%m%d")
  return date.strftime("%d/%m-%Y")


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
    return "Forkert formattering af cpr nr."

  # Check if digits and validate checksum
  if cpr.isdigit():
    cpr_int_arr = [int(i) for i in cpr]
    control_arr = [4,3,2,7,6,5,4,3,2,1]
    p_cpr = pandas.Series(cpr_int_arr)
    p_con = pandas.Series(control_arr)
  
    if (p_cpr * p_con).sum() % 11 == 0:
      return None

  return "Forkert formattering af cpr nr."


def check_name(name):
  if name == '':
    return "Intet navn angivet"
  
  if ' ' in name:
    return None

  return "Fornavn og efternavn skal udfyldes"


def check_date(date):
  """
  Checks whether a given study date is valid

  Args:
    date: study date to check, format (YYYYMMDD) or (YYYY-MM-DD)

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
            return "Fejlagtig dag i dato."
        else:
          return "Fejlagtig måned i dato."
      else:
        return "Dato må kun indeholde heltal og '-'."
    else:
      return "Forkert formattering af dato."

  return "Forkert formattering af dato."


def check_rigs_nr(rigs_nr):
  """
  Checks if a given RIGS nr is valid

  Args:
    rigs_nr: RIGS nr to check

  Returns:
    None if valid RIGS nr, otherwise returns a string containing an error message
  """
  if 'REGH' in rigs_nr:
    return None

  return "Accession nr. skal starte med 'REGH'."


def is_valid_study(cpr, name, study_date, accession_number):
  """
  Checks whether given study information is vaild.

  Args:
    cpr: cpr nr of patient
    name: name of patient
    study_date: date of the study
    rigs_nr: RIGS number of the study
  """
  errors = [ ]

  # Check cpr
  if cpr:
    if not re.match(r"^[a-zA-Z0-9\-]+$", cpr):
      errors.append("CPR nummer indeholder ulovlige karaktere.")
  else:
    errors.append("CPR nummer må ikke være tomt.")

  # Check name
  if not name:
    errors.append("Navn må ikke være tomt.")

  # Check study_date
  try:
    datetime.strptime(study_date, '%d-%m-%Y')
  except ValueError:
    errors.append("Dato har ikke korrekt format (tilladt format: DD-MM-ÅÅÅÅ).")

  # Check accession number
  if accession_number:
    if not re.search(r"\s", accession_number):
      if not re.match(r"^[a-zA-Z0-9\-]+$", accession_number):
        errors.append("Accession nummer indeholder ulovlige karaktere.")
    else:
      errors.append("Accession nummer må ikke indeholde mellemrum.")
  else:
    errors.append("Accession nummer må ikke være tomt.")

  return (errors == [ ]), errors


def name_to_person_name(name: str) -> str:
  """
  Converts a normally formatted name, e.g. "Jens Jensen" to a dicom person name
  (for more details see: http://dicom.nema.org/dicom/2013/output/chtml/part05/sect_6.2.html)
  
  Args:
    name: string with name to convert

  Returns:
    The formatted name conforming with the dicom standard.
  """
  # If the name is empty, return it
  if not name:
    return name

  # If the name is already a person name, return it
  if name.count('^') == 4:
    return name

  names = name.strip().split(' ')

  firstname = names[0]
  middlenames = names[1:-1]
  lastname = names[-1]

  ret = ""
  if middlenames:
    ret = lastname + '^' + firstname + '^' + ' '.join(middlenames)
  else:
    ret = lastname + '^' + firstname + '^'

  return ret + '^^'
  

def convert_cpr_to_cpr_number(cpr):
  """
  Takes a cpr number on format XXXXXX-XXXX, where X is numbers,
  and converts it to XXXXXXXXXX. If it's on format, returns the CPR number as is

  Args:
    cpr
  Ret:
    String 
  """
  try:
    if cpr[6] == '-':
      return cpr.replace('-','') 
    else:
      return cpr
  except IndexError:
    return cpr

def convert_american_date_to_reasonable_date_format(unreasonable_time_format):
  month, day, yearandtimestamp = unreasonable_time_format.split('/')
  year, timestamp = yearandtimestamp.split(' ')
  return f"{year}-{month}-{day} {timestamp}"

def reverse_format_date(reverse_Date : str, sep='') -> str:
  """
    Converts a string on format DDMMYYYY, DD-MM-YYYY or DD/MM/YYYY to YYYY{sep}MM{sep}DD

    Args:
      reverse_Date: string of format DDMMYYYY, DD-MM-YYYY or DD/MM/YYYY

    Kwargs:
      sep: String, this string is put in between the time

    Returns
      dateformat : String on format YYYYMMDD
      Returns '' on input = ''

    Raises:
      ValueError : On invalid String
    """ 
  if reverse_Date == None or reverse_Date == '':
    return ''
  # Argument checking
  if reverse_Date.count('-') == 2 and len(reverse_Date) == 10:
    day, month, year = reverse_Date.split('-')

    if day.isdigit() and month.isdigit() and year.isdigit():
      try:
        #Create datetime object to see if it's a valid date
        datetime(int(year), int(month), int(day)) 
      except ValueError as  V:
        raise ValueError('Reverse_format_date: Input string doesnt corrospond to a valid date')
    else:
      raise ValueError('Reverse_format_date: Date, Month or Years are not digits')
  
  elif reverse_Date.count('/') == 2 and len(reverse_Date) == 10:
    day, month, year = reverse_Date.split('/')

    if day.isdigit() and month.isdigit() and year.isdigit():
      try:
        #Create datetime object to see if it's a valid date
        datetime(int(year), int(month), int(day))  
      except ValueError as V:
        raise ValueError('Reverse_format_date: Input string doesnt corrospond to a valid date')
    else:
      raise ValueError('Reverse_format_date: Date, Month or Years are not digits')
  
  elif len(reverse_Date) == 8 and reverse_Date.isdigit():
    day = reverse_Date[:2]
    month = reverse_Date[2:4]
    year = reverse_Date[4:]

    try:
      #Create datetime object to see if it's a valid date
      datetime(int(year), int(month), int(day)) 
    except ValueError as V:
      raise ValueError('Reverse_format_date: Input string doesnt corrospond to a valid date')
  else:
    raise ValueError('Reverse_format_date: String is not on correct format')
# Converting format
  returnstring = year + sep + month + sep + day
  # Returning
  return returnstring

def convert_date_to_danish_date(date_str: str, sep: str='') -> str:
  """
  Converts a string from the format YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD to DD{sep}MM{sep}YYYY

  Args:
    date_str : String, on format  YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD, where the string corospond to a date
  
  Kwargs:
    sep : String, this string is put in between the time
  
  Returns:
    String on format DD{sep}MM{sep}YYYY
  """
  VALID_FORMATS = ('%Y%m%d', '%Y-%m-%d', '%Y/%m/%d')
  date = ''
  
  for date_format in VALID_FORMATS:
    try:
      date = datetime.strptime(date_str, date_format)
      break
    except ValueError:
      # Unable to parse, try next one
      continue
  
  if date:
    return date.strftime(f'%d{sep}%m{sep}%Y')
  
  raise ValueError(f"Unable to parse date string: '{date_str}'")


def xstr(s: str) -> str:
  """
  Args:
    s: string to transform

  Returns:
    s if s is not None, otherwise return an empty string

  Remark:
    This function exists since str will return 'None' for None objects, e.g.:

    >>> x = None
    >>> str(x)
    'None'
    >>> xstr(x)
    ''
  """
  if not s:
    return ''

  return str(s)

def splitDateTimeStr(input_str):
  """
    Converts a valid datestring from a dicom object to 2 strings on the format:
    date :  DD-MM-YYYY
    time :  tt:mm

    Args:
      input_str: string in on the format:

    returns:
      Date: See above
      Time: See above
  """
  if(len(input_str) != 12 and input_str.isdigit()):
    raise AttributeError('THIS IS NOT A VALID DATESTRING YOU BROKEN MY TRUST')

  year  = input_str[:4]
  month = input_str[4:6]
  day   = input_str[6:8]
  hour  = input_str[8:10]
  minut = input_str[10:]

  return f'{day}-{month}-{year}', f'{hour}:{minut}'


def float_safe(val: Union[str, int]) -> float:
  """
  Wrapper for safe conversion to float.
  Safe: commas are replaced with dots to better localization support

  Args:
    val: value to be cast to float

  Returns:
    The value converted to a float
  """
  if isinstance(val, str):
    val = val.replace(',', '.')

  return float(val)


def extract_request_parameters(
  d: dict,
  format_dict: dict
) -> dict:
  """
  Extracts and type safely type converts the request parameters

  Args:
    d: dict. of key, value pairs to be converted.
    format_dict: dict. of keys and their corresponding type to be converted to

  Returns:
    Dictionary containing the same key, value pair where the value has been
    converted acording to the format_dict

  Raises:
    ValueError: if a value failed to be converted
  """
  ret = { }

  for key, conv_type in format_dict.items():
    # Find corresponding value
    try:
      value = d[key]
    except KeyError:
      ValueError(f"Key: '{key}', is not in dictionary of values.")

    # Check if current entry should be processed as a list
    is_multi_value = isinstance(conv_type, tuple)
    if is_multi_value:
      _, new_type = conv_type
    else:
      new_type = conv_type

    # Convert every entry
    new_value = [ ]
    for sub_val in value:
      _sub_val = sub_val.strip()

      try:
        if new_type == float:
          new_value.append(float_safe(_sub_val)) # Handles dots and commas
        else:
          new_value.append(new_type(_sub_val))
      except ValueError:
        raise ValueError(f"Failed to convert key: '{key}', with value: '{_sub_val}'")
    
    # Only select first value if it's not a list
    if is_multi_value:
      ret[key] = new_value
    else:
      ret[key] = new_value[0]

  return ret

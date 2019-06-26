import calendar
import pandas
import re
from datetime import datetime


def person_name_to_name(name: str) -> str:
  """
  Formats dicom person names to names of form: Firstname [Middlenames] Lastnames

  Args:
    name: dicom person name

  Returns:
    the normally formatted name

  Remark:
    Specification for person names: http://dicom.nema.org/dicom/2013/output/chtml/part05/sect_6.2.html
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

  # danish cpr numbers should contain exactly 10 digits
  if not re.match(r"[0-9]{10}", cpr):
    raise ValueError(f"cpr: '{cpr}', doesn't contain exactly 10 digits")

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


def is_valid_study(cpr, name, study_date, rigs_nr):
  """
  Checks whether given study information is vaild.

  Args:
    cpr: cpr nr of patient
    name: name of patient
    study_date: date of the study
    rigs_nr: RIGS number of the study

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
  error_strings.append(check_rigs_nr(rigs_nr))

  # Filter out None values
  error_strings = list(filter(lambda x: x, error_strings))

  return (True, error_strings)


def name_to_person_name(name):
  """
  Converts a normally formatted name, e.g. "Jens Jensen" to a dicom person name
  VR formatting. 
  (for more details see: http://dicom.nema.org/dicom/2013/output/chtml/part05/sect_6.2.html)
  
  Args:
    name: string to convert

  Returns:
    The formatted name conforming with the dicom standard.

  Remark:
    This function also accepts and handles dicom wildcards.
  """
  name = name.strip()

  names = name.split(' ')

  firstname = names[0]
  middlenames = names[1:-1]
  lastname = names[-1]

  ret = ""
  if middlenames:
    ret = lastname + '^' + firstname + '^' + ' '.join(middlenames)
  else:
    ret = lastname + '^' + firstname

  return ret
  
def convert_cpr_to_cpr_number(cpr):
  """
  Takes a cpr number on format XXXXXX-XXXX, where X is numbers,
  and converts it to XXXXXXXXXX. If it's on format, returns the CPR number as is

  Args:
    cpr
  Ret:
    String 
  """

  if cpr[6] == '-':
    return cpr.replace('-','') 
  else:
    return cpr
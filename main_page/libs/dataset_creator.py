import logging
from pydicom import Dataset, Sequence, uid
from typing import Type
import inspect

from datetime import datetime, date

from . import dicomlib
from . import server_config
from . import formatting
from main_page import log_util

logger = log_util.get_logger(__name__)


# TODO: Possibly put this decorator function in a seperate file so it can be reused in other places
def none_check(func, kwargs_check=False):
  """
  Decorator which ensures that no argument, and optionally keyword arguments,
  are not None.

  Args:
    func: function to wrap (i.e. this is a decorator)

  Kwargs:
    kwargs_check: whether or not to also check keyword arguments

  Raises:
    ValueError: If an argument is found to be None

  Remarks:
    This decorator ONLY handles None, empty strings or 0 are still passable.
  """
  def wrapper(*args, **kwargs):
    arg_spec = inspect.getfullargspec(func).args
    
    # Check if any arg is None
    for i, arg in enumerate(args):
      if arg == None:
        raise ValueError(f"Got None for argument: {arg_spec[i]}")

    # Check if any kwarg is None, if specified
    if kwargs_check:
      for kwarg, kw_value in kwargs:
        if kw_value == None:
          raise ValueError(f"Got None for keyword argument: {kwarg}")

    # Successful return if all checks passed
    return func(*args, **kwargs)
  return wrapper


@none_check
def create_empty_dataset(accession_number: str) -> Type[Dataset]:
  """
  Constructs an empty pydicom dataset only with meta data filled out

  Args:
    accession_number: Accession number to use to generate the required UIDs

  Returns:
    The constructed dataset
  """
  # if not accession_number:
  #   raise ValueError(f'Unable to create dataset with accession_number: {accession_number}')
  ds = Dataset()

  # Set meta info in ds
  ds.is_little_endian = True
  ds.is_implicit_VR = True
  ds.add_new(0x00080005, 'CS', 'ISO_IR 100')
  ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.7' # SecondaryImageCapture
  ds.SOPInstanceUID = uid.generate_uid(prefix='1.3.', entropy_srcs=[accession_number, 'SOP'])

  # Move meta data into actual file_meta dataset
  ds.fix_meta_info()
  
  return ds


@none_check
def get_blank(
    cpr: str,
    name: str,
    study_date: str,
    accession_number: str,
    hospital_ae_title: str
  ) -> Type[Dataset]:
  """
  Generates a dataset with the minimum required information for performing
  a study. This function is to be used when users manually generate examinations
  through the 'nødopret' feature.

  Args:
    cpr: cpr number of patient
    name: name of patient
    study_date: date examination is to be performed (format: YYYY-MM-DD)
    accession_number: accession number of the examination
    hospital_ae_title: AET for scheduled station name - see dicom tags 0x00400001 and 0x004000010

  Returns:
    The generated dataset with filled out tags

  TODO: Validate the format of the study_date (possibly change it to take a date object instead)
  """
  # Create dataset w/ meta data
  ds = create_empty_dataset(accession_number)
  ds.RequestedProcedureDescription = 'GFR, Tc-99m-DTPA'
  # Fill out required examination data to allow the site to propperly use the dataset 
  method_str = 'GFR, Tc-99m-DTPA'
  
  study_instance_uid = uid.generate_uid(
    prefix='1.3.',
    entropy_srcs=[accession_number, 'Study']
  )
  ds.add_new(0x0020000d, 'UI', study_instance_uid)
  
  ds.add_new(0x0032000a, 'CS', 'STARTED')
  ds.add_new(0x00321060, 'LO',  method_str)

  # Create ScheduledProcedureStepSequence
  now = datetime.now()


  ds_seq = Dataset()
  ds_seq.add_new(0x00080060, 'CS', 'OT')
  ds_seq.add_new(0x00400001, 'AE', hospital_ae_title)
  ds_seq.add_new(0x00400002, 'DA', study_date.replace('-',''))
  ds_seq.add_new(0x00400003, 'TM', now.strftime('%H%M'))
  ds_seq.add_new(0x00400007, 'SH', method_str)
  ds_seq.add_new(0x00400010, 'SH', hospital_ae_title)

  ds.add_new(0x00400100, 'SQ', Sequence([ds_seq]))

  # Insert given information into dataset
  dicomlib.fill_dicom(
    ds,
    update_dicom=True,
    cpr=cpr,
    name=name,
    ris_nr=accession_number
  )

  return ds


def generate_ris_query_dataset(ris_calling: str='') -> Type[Dataset]:
  """
  Generates a dataset for quering RIS

  Args:
    ris_calling: AET for RIS station to retreive studies from, e.g. RH_EDTA, EDTA_GLO, etc.

  Returns:
    Generated dataset used to query rigs
  """
  # Create new dataset
  ds = Dataset()
  
  # Fill required tags, empty tags will be filled out by RIS
  # Non-empty tags with be used as search parameters
  ds.add_new(0x00080016, 'UI', '')      # SOPClassUID These values may be discarded
  ds.add_new(0x00080018, 'UI', '')      # SOPInstanceUID These values may be discarded
  ds.add_new(0x00080020, 'DA', '')      # Study date
  ds.add_new(0x00080050, 'SH', '')      # Accession Number
  ds.add_new(0x00080052, 'CS', 'STUDY') # Root SOP Class level
  ds.add_new(0x00081110, 'SQ', '')      # ReferencedStudySequence
  ds.add_new(0x00100010, 'PN', '')      # Patitent name
  ds.add_new(0x00100020, 'LO', '')      # PatientID / CPR NUMBER
  ds.add_new(0x00100030, 'DA', '')      # Patient Birthday #Why? do we query this, it's in CPR Number?
  ds.add_new(0x0020000D, 'UI', '')      # StudyInstanceUID
  ds.add_new(0x0020000E, 'UI', '')      # SeriesInstanceUID
  ds.add_new(0x00321060, 'LO', '')      # RequestedProcedureDescription

  # Create ScheduledProcedureStepSequence
  Sequenceset = Dataset() 
  
  Sequenceset.add_new(0x00080060, 'CS', 'OT')           # Modality
  Sequenceset.add_new(0x00400001, 'AE', ris_calling) # ScheduledStationAETitle
  Sequenceset.add_new(0x00400002, 'DA', '-' +date.today().strftime("%Y%m%d"))           # ScheduledProcedureStepStartDate
  Sequenceset.add_new(0x00400003, 'TM', '')           # ScheduledProcedureStepStartTime
  Sequenceset.add_new(0x00400007, 'LO', '')           # ScheduledProcedureStepDescription
  Sequenceset.add_new(0x00400009, 'SH', '')           # ScheduledProcedureStepID
  Sequenceset.add_new(0x00400010, 'SH', '')           # ScheduledStationName
  Sequenceset.add_new(0x00400011, 'SH', '')           # ScheduledProcedureStepLocation

  ds.add_new(0x00400100, 'SQ', Sequence([Sequenceset])) # ScheduledProcedureStepSequence

  return ds


def create_search_dataset(
    name: str,
    cpr: str,
    date_from: str,
    date_to: str,
    accession_number: str
  ) -> Type[Dataset]:
  """
  Creates a dataset for querying PACS

  Args:
    name: name of patient
    cpr: cpr of patient
    date_from: date to search from
    date_to: date to search to
    accession_number: accession number of examination
    stationName: AET for station name, e.g. RH_EDTA, EDTA_GLO, etc.

  Returns:
    The generated search dataset
  """
  ds = Dataset()

  # Correctly format the date search string
  date_from = date_from.replace('-','')
  date_to = date_to.replace('-','')
  
  if date_from != '' or date_to != '':
    ds.StudyDate = f"{date_from}-{date_to}"
  else:
    ds.StudyDate = ''

  # Fill dataset with additional information
  ds.AccessionNumber = accession_number
  ds.PatientID = cpr
  ds.PatientName = formatting.name_to_person_name(name)
  ds.QueryRetrieveLevel = 'STUDY'
  ds.SOPClassUID = ''
  ds.SOPInstanceUID = ''
  ds.SeriesInstanceUID = ''
  ds.StudyInstanceUID = ''
  ds.Modality = 'OT'
  ds.StudyID = 'GFR*'

  return ds

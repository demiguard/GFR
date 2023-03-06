import pathlib
import datetime
import glob
import shutil

from pydicom import Dataset
from typing import List

from main_page.libs import dicomlib
from main_page.libs import server_config
from main_page import log_util

logger = log_util.get_logger(__name__)

def filter_dicom(dicom_list, tag, tag_value):
  passed = []
  failed = []

  for dicom_obj in dicom_list:
    if tag in dicom_obj:
      if dicom_obj[tag] == tag_value:
        passed.append(dicom_obj)
      else:
        failed.append(dicom_obj)
    else:
      failed.append(dicom_obj)

  return passed, failed


def get_history(dataset, active_hospital):
  """
  Retrives Historical information about a study

  Args:
    cpr: string The cpr number without a string
    age: Datetime object with day of birth

  Returns:
    date_list:            A datetime-list. The n'th element is a datetime object with time of examination. The lenght is 'm'
    age_list:             A float list. Element is calculated age at time of examination. The lenght is 'm'
    clearence_norm_list:  A float list. The n'th element is float
  """
  #Init
  age_list            = []
  clearence_norm_list = []
  date_list           = []
  history_sequence    = []

  birthday = datetime.datetime.strptime(dataset.PatientBirthDate,'%Y%m%d') 

  #Get all file paths for the Accession number
  curr_dicom_path = f"{server_config.FIND_RESPONS_DIR}{active_hospital}/{dataset.AccessionNumber}/{dataset.AccessionNumber}.dcm"
  dicom_filepaths = glob.glob(f'{server_config.FIND_RESPONS_DIR}{active_hospital}/{dataset.AccessionNumber}/*.dcm')
  #Filter the already opened dataset out
  history_filepaths = filter(lambda x: x != curr_dicom_path, dicom_filepaths)

  #Iterate through the datasets
  for history_filepath in history_filepaths:
    #Open the dataset
    history_dataset = dicomlib.dcmread_wrapper(history_filepath)
    #Create History dataset for history datasets
    try:
      date_of_examination = datetime.datetime.strptime(history_dataset.StudyDate,'%Y%m%d')
      age_at_examination = (date_of_examination - birthday).days / 365

      age_list.append(age_at_examination)
      date_list.append(date_of_examination)
      clearence_norm_list.append(history_dataset.normClear)

      #Dataset for dicom
      sequence_dataset = Dataset()
      sequence_dataset.AccessionNumber  = history_dataset.AccessionNumber
      sequence_dataset.StudyDate        = history_dataset.StudyDate
      sequence_dataset.PatientSize      = history_dataset.PatientSize
      sequence_dataset.PatientWeight    = history_dataset.PatientWeight
      #Private tags
      sequence_dataset.clearance        = history_dataset.clearance
      sequence_dataset.normClear        = history_dataset.normClear
      sequence_dataset.ClearTest        = history_dataset.ClearTest
      sequence_dataset.injTime          = history_dataset.injTime
      history_sequence.append(sequence_dataset)
    except AttributeError as E:
      logger.error(f'Sequence dataset {history_filepath} has invalid format with {E}')

  dicomlib.fill_dicom(dataset, dicom_history=history_sequence)

  return date_list, age_list, clearence_norm_list


def get_studies(directory: str) -> List[Dataset]:
  """
  Get the list of studies from a directory

  Programmer Remarks:
    This is not specific enough to be in ris_query_wrapper and should be moved to an
    appropriate folder

  Args:
    directory: path to directory containing studies

  Returns:
    List of pydicom datasets of all studies currently in the
    datasets_dir directory
  """
  datasets = [ ]

  for dataset_dir in pathlib.Path(directory).glob('*'):
    accession_number = dataset_dir.name
    dataset_dir = f"{directory}/{accession_number}"
    dataset_filepath = f"{dataset_dir}/{accession_number}.dcm"

    try:
      datasets.append(dicomlib.dcmread_wrapper(dataset_filepath))
    except FileNotFoundError:
      # The sub file doesn't exist, delete the directory
      logger.info(f"Deleting directory, due to missing dicom file in dataset directory: \"{dataset_dir}\"")
      shutil.rmtree(dataset_dir)

  return datasets
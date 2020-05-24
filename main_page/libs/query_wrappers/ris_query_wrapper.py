import glob
import os
import datetime
import random
import shutil
import pydicom
from pydicom import Dataset
import pynetdicom
import logging
from pathlib import Path

from typing import List, Tuple, Type

from main_page import models
from main_page.libs import formatting
from main_page.libs import server_config
from main_page.libs import dataset_creator
from main_page.libs import dicomlib
from main_page.libs.dirmanager import try_mkdir
from main_page.libs.clearance_math import clearance_math


from main_page import log_util

logger = log_util.get_logger(__name__)

"""
This module contains functions for working with studies/datasets received
from RIS. datasets are retreieved by the background thread RIS_thread,
which periodically queries RIS for any new datasets and stores them in the
directory specified in: server_config.FIND_RESPONS_DIR
"""


def permanent_delete(
  dataset: Type[Dataset],
  hospital_shortname: str,
  deleted_studies_dir: str=server_config.DELETED_STUDIES_DIR
) -> bool:
  """
  Permanently deletes a study from the server's system

  Args:
    dataset: dataset to move from active to deleted
    hospital_shortname: abbreviation for hospital name 
                        (e.g. "RH" for Rigshospitalet)

  Kwargs:
    deleted_studies_dir: directory containing deleted studies

  Returns:
    True if the move succeeded, False otherwise
  """
  try:
    study_dir = Path(
      deleted_studies_dir,
      hospital_shortname,
      dataset.AccessionNumber
    )
  except AttributeError:
    return False

  try:
    shutil.rmtree(study_dir)
  except Exception:
    return False

  return True


def move_to_deleted(
  dataset: Type[Dataset],
  hospital_shortname: str,
  active_studies_dir: str=server_config.FIND_RESPONS_DIR, 
  deleted_studies_dir: str=server_config.DELETED_STUDIES_DIR
  ) -> bool:
  """
  Moves a dataset from active_studies_dir to deleted_studies_dir

  Args:
    dataset: dataset to move from active to deleted
    hospital_shortname: abbreviation for hospital name 
                        (e.g. "RH" for Rigshospitalet)

  Kwargs:
    active_studies_dir: directory containing active studies
    deleted_studies_dir: directory containing deleted studies

  Returns:
    True if the move succeeded, False otherwise
  """
  try:
    accession_number = dataset.AccessionNumber
  except AttributeError:
    return False

  deleted_dir_loc = Path(deleted_studies_dir, hospital_shortname)
  try_mkdir(deleted_dir_loc, mk_parents=True)

  active_file = Path(
    active_studies_dir,
    hospital_shortname,
    accession_number
  )

  deleted_file = Path(
    deleted_dir_loc,
    accession_number
  )

  #There already exists a deleted file delete it then move the old over
  if deleted_file.exists():
    shutil.rmtree(deleted_file.as_posix())

  shutil.move(active_file.as_posix(), deleted_file.as_posix())

  return True


def check_if_old(
  datasets: List[Dataset],
  hospital_shortname: str,
  process,
  *args,
  threshold: int=7,
  **kwargs
  ) -> Tuple[List[Dataset], List[Dataset]]:
  """
  Checks if a list of datasets are older than a given number of days, 
  if a dataset is to old then call the function process with 
  the dataset, hospital_shortname, args and kwargs as parameters.
  
  The process function should return True if the processing succeeded, False
  otherwise.

  Args:
    datasets: pydicom datasets to check through

  Kwargs:
    threshold: number of days a dataset is allowed be active for

  Returns:
    Tuple of two lists; first list contains all datasets which are within 
    the threshold. Second list contains datasets which failed to be processed.

  Remarks:
    First checks StudyDate, if it's unavailable then attempts to use
    ScheduleProcedureStepStartDate, if this too is unavailable the dataset
    will be appended to the failed_datasets lists which are unable to parse
  """
  valid_datasets = [ ]
  failed_datasets = [ ]

  today = datetime.datetime.today()

  for dataset in datasets:
    # Attempt determine study_date for dataset
    # first check recovery date if the study has been previously recovered
    recover_date = dicomlib.get_recovered_date(
      dataset.AccessionNumber, hospital_shortname
    )
    
    if recover_date:
      study_date_str = recover_date
    else:
      study_date_str = dicomlib.get_study_date(dataset)

    if not study_date_str:  
      failed_datasets.append(dataset)
      continue
    
    # Attempt to convert to datetime.datetime object in order to check threshold
    try:
      study_date = datetime.datetime.strptime(study_date_str, "%Y%m%d")
    except ValueError:
      failed_datasets.append(dataset)
      continue

    day_diff = int((today - study_date).days)

    if day_diff <= threshold:
      # It's valid, keep it
      valid_datasets.append(dataset)
    else:
      # It's invalid, apply action
      action_resp = process(dataset, hospital_shortname, *args, **kwargs)
      
      if not action_resp: # Action failed
        failed_datasets.append(dataset)
        continue

  return valid_datasets, failed_datasets


def procedure_filter(
  datasets: List[Dataset],
  blacklist: List[str]
) -> List[Dataset]:
  """
  Filters out any datasets which have a procedure type which is blacklisted

  Args:
    datasets: datasets to filter through
    blacklist: list strings of procedure types which are blacklisted

  Returns:
    List of datasets which don't have a procedure type on the blacklist
  """
  ret = [ ]
  
  for dataset in datasets:
    try:
      procedure = dataset.StudyDescription

      if not procedure:
        raise AttributeError
    except AttributeError:
      try:
        procedure = dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription
      except (IndexError, AttributeError):
        ret.append(dataset)

    if procedure not in blacklist:
      ret.append(dataset)

  return ret


def sort_datasets_by_date(
  datasets: List[Dataset], 
  reverse: bool=True
  ) -> List[Dataset]:
  """
  Sorts a list of pydicom datasets by date

  Args:
    datasets: list of datasets to sort

  Kwargs:
    reverse: whether to sort in decending or ascending order

  Returns:
    Sorted list of datasets

  Remarks:
    The datasets are sorted first based on the ScheduledProcedureStepStartDate
    within ScheduledProcedureStepSequence. If non of these are present in the
    dataset, then it attempts to use StudyDate. If StudyDate fails, then a
    dataset will default to 0.
  """
  # Sort based on date in descending order
  def date_sort(dataset):
    try:
      return int(dicomlib.get_study_date(dataset))
    except (TypeError, ValueError): # None and '' conversion fail
      return 0

  return sorted(datasets, key=date_sort, reverse=reverse)


def extract_list_info(
  datasets: List[Dataset]
  ) -> Tuple[List[dict], List[Dataset]]:
  """
  Extracts information from a list of datasets to be displayed in list_studies

  Args:
    datasets: list of pydicom datasets to extract infomation from for list_studies

  Returns:
    Tuple of two list, first being a list of dict each contaning the extracted
    information. The second list are all pydicom datasets which failed to have
    information extracted, due to missing attributes
  """
  registered_studies = [ ]
  failed_studies = [ ] # List of accession numbers for studies which failed to have data extracted    

  for dataset in datasets:
    try:
      procedure = dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription
    except AttributeError:
      try:
        procedure = dataset.StudyDescription
      except AttributeError:
        failed_studies.append(dataset)
        continue

    study_date = dicomlib.get_study_date(dataset)
    if not study_date:
      failed_studies.append(dataset)
      continue
    
    study_date = datetime.datetime.strptime(study_date, "%Y%m%d")
    study_date = study_date.strftime("%d-%m-%Y")

    try:
      exam_status = dataset.ExamStatus
    except AttributeError:
      exam_status = 0

    try:
      registered_studies.append({
        'accession_number': dataset.AccessionNumber,
        'cpr'             : formatting.format_cpr(dataset.PatientID),
        'study_date'      : study_date,
        'procedure'       : procedure,
        'name'            : formatting.person_name_to_name(str(dataset.PatientName)),
        'exam_status'     : exam_status
      })
    except AttributeError: # Unable to find tag in dataset
      failed_studies.append(dataset)
      continue

  return registered_studies, failed_studies


def get_studies(
  directory: str, 
  ) -> List[Dataset]:
  """
  Get the list of studies from a directory

  Args:
    directory: path to directory containing studies
    
  Returns:
    List of pydicom datasets of all studies currently in the
    datasets_dir directory
  """
  datasets = [ ]

  for dataset_dir in Path(directory).glob('*'):
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

import glob
import os
import datetime
import random
import shutil
import pydicom
from pydicom import Dataset
import pynetdicom
import logging

from typing import List, Tuple, Type

from main_page import models
from main_page.libs import formatting
from main_page.libs import server_config
from main_page.libs import dataset_creator
from main_page.libs import dicomlib
from main_page.libs import examination_info
from main_page.libs.dirmanager import try_mkdir
from main_page.libs.clearance_math import clearance_math
from main_page.libs.examination_info import ExaminationInfo

logger = logging.getLogger()


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
      return int(dataset.ScheduledProcedureStepSequence[0]
                 .ScheduledProcedureStepStartDate)
    except AttributeError: 
      # ScheduledProcedureStepSequence or ScheduledProcedureStepStartDate
      # not present in dataset
      try:
        return int(dataset.StudyDate)
      except (AttributeError, ValueError):
        # StudyDate not present in dataset or failed to convert it's value
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
        failed_studies.append(dataset.AccessionNumber)
        continue

    try:
      study_date = dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
    except AttributeError: 
      # ScheduledProcedureStepSequence or ScheduledProcedureStepStartDate
      # not present in dataset
      try:
        study_date = dataset.StudyDate
      except AttributeError:
        failed_studies.append(dataset.AccessionNumber)
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
        'cpr'             : dataset.PatientID,
        'study_date'      : study_date,
        'procedure'       : procedure,
        'name'            : formatting.person_name_to_name(str(dataset.PatientName)),
        'exam_status'     : exam_status
      })
    except AttributeError: # Unable to find tag in dataset
      failed_studies.append(dataset.AccessionNumber)
      continue

  return registered_studies, failed_studies


def dataset_is_valid(dataset: Type[Dataset], accession_numbers: List[str], accepted_procedures: List[str]) -> bool:
  """
  Validates the current new dataset

  Args:
    dataset: the current new dataset being processed
    accession_numbers: current list of accession number which have been processed
    accepted_procedures: list of accepted procedure descriptions within the user instance

  Returns:
    True if the dataset is valid and should be kept, False otherwise
  """
  has_been_processed = dataset.AccessionNumber not in accession_numbers
  is_accepted_procedure = (dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription not in accepted_procedures) or (accepted_procedures == [])
  has_been_handled = not models.HandledExaminations.objects.filter(accession_number=dataset.AccessionNumber).exists()

  return has_been_processed and is_accepted_procedure and has_been_handled


def has_expired(study_date: Type[datetime.datetime], today=datetime.datetime.now()) -> bool:
  """
  Determines whether a study has expired

  Args:
    study_date: date study was made
  
  Kwargs:
    today: the current date and time

  Returns:
    True if a study date has expired, False otherwise
  """
  return (today - study_date).days > server_config.DAYS_THRESHOLD


def log_connection_failed(config: Type[models.Config]) -> None:
  """
  Log that the connection to RIS failed
  """
  logger.warn(
    f"""Could not connect to RIS with:
        IP: {config.ris_ip}
        port: {config.ris_port}
        calling AET: {config.ris_calling}
        RIS AET: {config.ris_aet}
    """
  )


def log_connection_success(config: Type[models.Config]) -> None:
  """
  Log that the connection to RIS succeded
  """
  logger.info(
    f"""Connected to RIS with:
        IP: {config.ris_ip},
        port: {config.ris_port},
        calling AET: {config.ris_calling},
        RIS AET: {config.ris_aet}
    """
  )


def connect_to_RIS(config: Type[models.Config]):
  """
  Attempts to establish a connection to RIS via. the given configuration

  Args:
    config: Config model instance, describing the connection RIS

  Returns:
    If successful, the assosication to RIS

  Raises:
    ConnectionError: if any error occured during the attempt 
                     to establish a connection to RIS
  """
  try:
    ae = pynetdicom.AE(ae_title=config.ris_calling)
  except ValueError:
    # If AET is empty then a ValueError is thrown by pynetdicom
    log_connection_failed(config)
    raise ConnectionError("Kunne ikke forbinde til RIS, der fremvises kun tidligere hentede undersøgelser.")

  FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.1'
  ae.add_requested_context(FINDStudyRootQueryRetrieveInformationModel)

  assocation = ae.associate(
    config.ris_ip,
    int(config.ris_port), # Portnumbers should be shorts or ints! - TODO: update our database to store integers intead of CharFields to avoid this type cast, as it might fail
    ae_title=config.ris_aet
  )

  if assocation.is_established:
    log_connection_success(config)
  else:
    log_connection_failed(config)
    raise ConnectionError("Kunne ikke forbinde til RIS, der mangler måske nye undersøgelser")

  return assocation


def get_registered_studies(
  active_datasets_dir: str, 
  hospital_shortname: str) -> List[Dataset]:
  """
  Get the list of currently registered studies

  Args:
    active_datasets_dir: path to directory containing active dicom objects
    hospital_shortname: abbreviated hospital name 
    (e.g. 'RH' for 'Rigshospitalet', 'GLO' for 'Glostrup Hospital')

  Returns:
    List of pydicom datasets of all registered studies currently in the
    active_datasets_dir directory

  Remarks:
    This function will retrieve all patients from the active_datasets_dir,
    including ones from previous dates.
  """
  hospital_dir = f"{active_datasets_dir}{hospital_shortname}"
  hospital_dir_wildcard = f"{hospital_dir}/*"

  datasets = [ ]

  for dataset_dir in glob.glob(hospital_dir_wildcard):
    accession_number = dataset_dir.split('/')[-1]
    dataset_filepath = f"{hospital_dir}/{accession_number}/{accession_number}.dcm"
    
    datasets.append(dicomlib.dcmread_wrapper(dataset_filepath))

  return datasets


# TODO: This below function is depricated and is being phased out! (use get_registered_studies instead)
def get_patients_from_rigs(user):
  """
  Args:
    user: instance of Django User model who is making the call to RIS

  Returns:
    pydicom Dataset List : with all patients availble to the server  
    Error message : If an error happens it's described here, if no error happened, returns an empty string

  Raises:
    a bunch of errors...
  """
  user_hospital = user.department.hospital
  user_config = user.department.config

  DATASET_AVAILABLE = 0xFF00
  NO_MORE_FILES_AVAILABLE = 0x0000

  studies = [ ]
  processed_accession_numbers = [ ] # List of accession numbers which have been processed
  accepted_procedures = [procedure.type_name for procedure in user_config.accepted_procedures.all()]

  # Find all previous dicom objects which have not passed the expiration day threshold
  try_mkdir(f"{server_config.FIND_RESPONS_DIR}{user_hospital.short_name}", mk_parents=True)

  dcm_file_paths = glob.glob(f'{server_config.FIND_RESPONS_DIR}{user_hospital.short_name}/*.dcm')

  for dcm_file_path in dcm_file_paths:
    dataset = dicomlib.dcmread_wrapper(dcm_file_path) # TODO: Should this not be working on a ExaminaitonInfo object not the dicom object itself? I.e. possibly make dicomlib.dcmread_wrapper return a ExaminationInfo instance to eleminate all direct access with dicom objects within our code
    date_string = dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
    date_of_examination = datetime.datetime.strptime(date_string,'%Y%m%d')
  
    if not has_expired(date_of_examination): # Not expired
      if dataset_is_valid(dataset, processed_accession_numbers, accepted_procedures):
        studies.append(dataset)
        processed_accession_numbers.append(dataset.AccessionNumber)
    else: # expired
      # TODO: Move to recycle bin
      logger.info('Old file detected moving {0}.dcm to recycle bin'.format(
        dataset.AccessionNumber
      ))
      try_mkdir(f"{server_config.DELETED_STUDIES_DIR}{user_hospital.short_name}", mk_parents=True)
      dest_path = f"{server_config.DELETED_STUDIES_DIR}{user_hospital.short_name}/{dataset.AccessionNumber}.dcm"
      shutil.move(dcm_file_path, dest_path) 


  # Attempt to connect to RIS
  try:
    assocation = connect_to_RIS(user_config)
  except ConnectionError as e:
    # Display error to user, if unable to establish connection to RIS
    # NOTE: Still returns any previously found dicom objects
    return studies, str(e)

  # Create query file to get new studies
  query_ds = dataset_creator.generate_ris_query_dataset(ris_calling=user_config.ris_calling)
  
  logger.info(f'User: {user.username} is making a C-FIND')
  logger.info(f"With accepted_procedures: {accepted_procedures}")
  
  response = assocation.send_c_find(query_ds, query_model='S')

  # Process response datasets
  for status, dataset in response:
    if status.Status == DATASET_AVAILABLE:
      logger.info(f'Recieved Dataset:{dataset.AccessionNumber}')
      
      # Validate dataset and ensure it doesn't already exist
      if dataset_is_valid(dataset, processed_accession_numbers, accepted_procedures):
        dataset_path = f'{server_config.FIND_RESPONS_DIR}{user_hospital.short_name}/{dataset.AccessionNumber}.dcm'
        deleted_dataset_path = f'{server_config.DELETED_STUDIES_DIR}{user_hospital.short_name}/{dataset.AccessionNumber}.dcm'
        
        if not ((os.path.exists(dataset_path)) or (os.path.exists(deleted_dataset_path))):
          try_mkdir(f"{server_config.FIND_RESPONS_DIR}{user_hospital.short_name}", mk_parents=True)
        
          dicomlib.save_dicom(
            dataset_path,
            dataset
          )
          
          studies.append(dataset)
          processed_accession_numbers.append(dataset.AccessionNumber)
      else:
        # Discard dataset object, if already processed
        continue
    elif status.Status == NO_MORE_FILES_AVAILABLE:
      logger.info("Query completed with no errors")
      continue
    else:
      logger.warn(f"Got unknown status code: {hex(status.Status)}")
  
  # Deallocate assocation after processing each received object
  assocation.release()

  return studies, ''

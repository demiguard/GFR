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
from main_page.libs import server_config
from main_page.libs import dataset_creator
from main_page.libs import dicomlib
from main_page.libs import examination_info
from main_page.libs.dirmanager import try_mkdir
from main_page.libs.clearance_math import clearance_math
from main_page.libs.examination_info import ExaminationInfo

logger = logging.getLogger()


def parse_bookings(resp_dir: str):
  """
  Get dicom objects for all responses

  Args:
    resp_dir: path to directory containing dicom responses from findscu

  Returns:
    dict of dicom objects for all responses
  """
  ret = { }

  # Loop all responses
  for dcm_path in glob.glob('{0}/rsp*.dcm'.format(resp_dir)):
    ret[dcm_path] = dicomlib.dcmread_wrapper(dcm_path)

  return ret


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
  is_accepted_procedure = (dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription in accepted_procedures) or (accepted_procedures == [])
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
      
      # Validate dataset
      if dataset_is_valid(dataset, processed_accession_numbers, accepted_procedures):
        dicomlib.save_dicom(
          f'{server_config.FIND_RESPONS_DIR}{user_hospital.short_name}/{dataset.AccessionNumber}.dcm',
          dataset
        )
        
        studies.append(dataset)
        processed_accession_numbers.append(dataset.AccessionNumber)
      else:
        # Discard object, if already processed
        continue
    elif status.Status == NO_MORE_FILES_AVAILABLE:
      logger.info("Query completed with no errors")
      continue
    else:
      logger.warn(f"Got unknown status code: {hex(status.Status)}")
  
  # Deallocate assocation after processing each received object
  assocation.release()

  return studies, ''

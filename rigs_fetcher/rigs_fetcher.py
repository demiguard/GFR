#!/usr/bin/env python3
import os
import logging
import sqlite3
import pydicom
import pynetdicom

from repeat_exec import RepeatedExec
from config import *


def execute_query(conn, query, query_args):
  """
  Executes a given query

  Args:
    conn: database connection
    query: string contaning the query
    query_args: dict containing additional arguments for the query

  Returns:
    the .fetchall() response from executing the query 
  """
  cursor = conn.cursor()
  
  cursor.execute(query, query_args)
  conn.commit()

  return cursor.fetchall()


def is_handled(conn, rigs_nr):
  """
  Checks whether a rigs_nr has already been handled

  Args:
    conn: database connection
    rigs_nr: rigs number to check

  Returns:
    True if it has been handled, False otherwise
  """
  handled_query = """
    SELECT *
    FROM main_page_handledexaminations he
      WHERE he.rigs_nr=:rigs_nr;
  """

  resp = execute_query(conn, handled_query, {'rigs_nr': rigs_nr})

  return (resp != [])


def create_base_dataset(calling_aet=''):
  """
  Makes a dataset matching Base_search_query

  This mainly a speed upgrade since we do not need to open a file

  Args:
    calling_ae_title : string 
  Returns:
    dataset: Pydicom dataset, matching that of base_rigs_query.dcm
  """
  # Create new dataset
  ds = pydicom.Dataset()
  
  ds.add_new(0x00080016, 'UI', '') #SOPClassUID These values may be discarded
  ds.add_new(0x00080018, 'UI', '') #SOPInstanceUID These values may be discarded
  ds.add_new(0x00080020, 'DA', '') #Study date
  ds.add_new(0x00080050, 'SH', '') #Accession Number
  ds.add_new(0x00080052, 'CS', 'STUDY') #Root SOP Class level
  ds.add_new(0x00081110, 'SQ', '')
  ds.add_new(0x00100010, 'PN', '') #Patitent name
  ds.add_new(0x00100020, 'LO', '') #PatientID / CPR NUMBER
  ds.add_new(0x00100030, 'DA', '') #Patient Birthday #Why? do we query this, it's in CPR Number?
  ds.add_new(0x0020000D, 'UI', '')
  ds.add_new(0x0020000E, 'UI', '')
  ds.add_new(0x00321060, 'LO', '')

  # Create sequence
  sequence = pydicom.Dataset() # ScheduledProcedureStepSequence
  
  sequence.add_new(0x00080060, 'CS', '')
  sequence.add_new(0x00400001, 'AE', calling_aet)
  sequence.add_new(0x00400002, 'DA', '')
  sequence.add_new(0x00400003, 'TM', '')
  sequence.add_new(0x00400007, 'LO', '')
  sequence.add_new(0x00400009, 'SH', '')
  sequence.add_new(0x00400010, 'SH', '')

  # adding sequence tag
  ds.add_new(0x00400100, 'SQ', pydicom.Sequence([sequence]))

  return ds


#res = is_handled(conn, 'REGH99999999')  # Test : True
#res = is_handled(conn, 'REGH12345678') # Test : False
#print(res)

def get_bookings(conn, calling_aet, rigs_ip, rigs_port, rigs_aet, accepted_procedures, storage_directory):
  logger = logging.getLogger()
  logger.info("##### TICK START #####")
  logger.info(f"Get bookings called - calling_aet: {calling_aet}")

  # Query RIGS for all bookings
  # Establish assocation/connection to RIGS
  ae = pynetdicom.AE(ae_title=calling_aet)

  StudyRootQueryRetrieveInformationModelFind = '1.2.840.10008.5.1.4.1.2.2.1'
  DATASET_AVAILABLE_STATUS = 0xFF00
  STUDY_MODEL = 'S'

  logger.info(f"Adding requested context: {StudyRootQueryRetrieveInformationModelFind}")
  ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

  logger.info(f"Trying to establish assocation with parameters - rigs_ip: {rigs_ip}, rigs_port: {rigs_port}, rigs_aet: {rigs_aet}")
  assocation = ae.associate(
    rigs_ip,
    rigs_port,
    ae_title=rigs_aet
  )

  if assocation.is_established:
    logger.info("Success: Established connection to RIGS")

    # Construct query dataset
    query_dataset = create_base_dataset(calling_aet=calling_aet)
    
    resp = assocation.send_c_find(query_dataset, query_model=STUDY_MODEL)

    for status, dataset in resp:
      logger.info(f"Got response with status: {hex(status.Status)}")
      
      if status.Status == DATASET_AVAILABLE_STATUS:
        logger.info(f"Got dataset: {dataset}")
        process_dataset(conn, dataset, accepted_procedures, storage_directory)
      else:
        logger.info("Got response without dataset")
  else:
    logger.warn("Failed to establish connection to RIGS")

  logger.info("##### TICK DONE #####\n\n\n\n")


def save_dicom(file_path, dataset, default_error_handling=True):
  """
  Saves a dicom file to a selected file path, and resolves issues related
  to metadata

  Args:
    file_path: String, desination for file to be saved
    dataset: dataset to save

  kwargs:
    no_error: With default dicom handling
  Raises
    Attribute Error: Incomplete Dicom, without default errorhandling
    Value Error: No given AccessionNumber
  """
  logger = logging.getLogger()

  dataset.is_implicit_VR = True
  dataset.is_little_endian = True

  if 'SOPClassUID' in dataset and 'SOPInstanceUID' in dataset:  # Dicom is incomplete
    if default_error_handling: 
      if 'AccessionNumber' in dataset:
        dataset.SOPClassUID = '1.2.840.10008.5.1.4.1.1.7' #S econdary Image Capture
        dataset.SOPInstanceUID = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[dataset.AccessionNumber, 'SOP'])
      else:
        raise ValueError('default Error handling for saving dicom failed!\nCannot create SOPInstanceUID without AccessionNumber!')
  else: 
    raise AttributeError('Incomplete Dicom Required Tags are SOPClassUID and SOPInstanceUID')
  
  dataset.fix_meta_info()

  logger.info('Saving Dicom file at:{0}'.format(file_path))

  dataset.save_as(file_path, write_like_original=False)


def process_dataset(conn, dataset, accepted_procedures, storage_directory):
  """
  Filter datasets based on which have been handled and on 
  the list of accepted procedures

  Args:
    dataset: current dataset to process
  """
  logger = logging.getLogger()
  logger.info("Processing dataset")

  # Check if procedure is accepted
  procedure = dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription

  if procedure not in accepted_procedures:
    return

  logger.info("Passed procedure check")

  # Check if handled
  rigs_nr = str(dataset.AccessionNumber)

  if is_handled(conn, rigs_nr):
    return

  logger.info("Passed handled check")

  # Check if already in storage_directory
  storage_path = f"{storage_directory}/{rigs_nr}.dcm"

  if os.path.exists(storage_path):
    return

  logger.info("Passed filepath check")

  # Passed all validation check - save
  save_dicom(storage_path, dataset)
  logger.info(f"Saved dataset to: {storage_path}")


def init_logger(log_filepath, log_level):
  logging.basicConfig(
    filename=log_filepath, 
    level=log_level, 
    format='%(asctime)s (%(filename)s/%(funcName)s) - [%(levelname)s] : %(message)s'
  )


def main():
  # Initialize logger
  init_logger(LOG_FILEPATH, LOG_LEVEL)

  # Connect to database
  conn = sqlite3.connect(DB_FILEPATH)

  # Construct function repeater
  repeater = RepeatedExec(
    INTERVAL,
    get_bookings,
    conn,
    CALLING_AET,
    RIGS_IP,
    RIGS_PORT,
    RIGS_AET,
    ACCEPTED_PROCEDURES,
    STORAGE_DIRECTORY,
    interval_variance=INTERVAL_VARIANCE
  )
  
  repeater.start()


if __name__ == '__main__':
  main()
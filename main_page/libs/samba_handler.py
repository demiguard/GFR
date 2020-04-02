import glob
import os
from datetime import datetime, date
import tempfile
from tempfile import NamedTemporaryFile
import logging
import pandas as pd
from pandas.errors import ParserError
from typing import List, Union

from . import server_config
from smb.SMBConnection import SMBConnection
from smb.base import OperationFailure, NotConnectedError
from . import formatting


from main_page import log_util

logger = log_util.get_logger(__name__)


def open_csv_file(temp_file: NamedTemporaryFile):
  """
  Opens a CSV file 

  Args:
    temp_file an already opened file

  Returns
    pandas File
  """
  try:
    pandas_ds = pd.read_csv(temp_file.name)
    protocol = pandas_ds['Protocol name'][0]
    datestring = pandas_ds['Measurement date & time'][0].replace('-','').replace(' ','').replace(':','')
  except ParserError:
    # Hidex file
    pandas_ds = pd.read_csv(temp_file.name, skiprows=[0,1,2,3])
    pandas_ds = pandas_ds.rename(
      columns={
        'Time'                    : 'Measurement date & time',
        'Vial'                    : 'Pos',
        'Normalized Tc-99m (CPM)' : 'Tc-99m CPM',
        'Tc-99m (counts)'         : 'Tc-99m Counts'
      }
    )

    # Because Hidex is in american format, we change the data column to the ONLY CORRECT format
    pandas_ds['Measurement date & time'] = pandas_ds['Measurement date & time'].apply(formatting.convert_american_date_to_reasonable_date_format)

    datestring = pandas_ds['Measurement date & time'][0].replace('-','').replace(' ','').replace(':','')
    # Get protocol
    temp_file.seek(0)
    protocol = temp_file.readline()
    
    temp_file.seek(0)

    # Hidex might store these as bytes - convert them to str
    logger.debug(f"Type protocol: {type(protocol)} with value: {protocol}")

    if isinstance(protocol, bytes):
      logger.debug(f"Converting bytes protocol to string.")
      protocol = protocol.decode()
      protocol = protocol.replace("\n", "")
      protocol = protocol.replace("\r", "")
      protocol = protocol.replace("\"", "")
  
  return pandas_ds, datestring, protocol


def move_to_backup(smb_conn, temp_file, hospital: str, fullpath: str, filename: str, model_server_config) -> None:
  """
  Moves a file from the Samples file to the backup folder.
  TODO: Try and reduce the amount of arguments

  Args:
    smb_conn: An Active SMBConnection
    temp_file: A File object with a write method
    hospital:
    fullpath:
    filename:

  Returns:
    .............
  """
  backup_folder = f"{server_config.samba_backup}/{hospital}"
  store_path = f"{backup_folder}/{filename}"
  share_name = model_server_config.samba_share

  try:
    smb_conn.createDirectory(share_name, u'/backup')
  except:
    logger.debug("Samba Info: Failed to create directory '/backup'")

  try:
    smb_conn.createDirectory(share_name, f'backup/{hospital}'.encode())
  except:
    logger.debug(f"Samba Info: Failed to create directory '/backup/{hospital}'")

  smb_conn.storeFileFromOffset(
    share_name,
    store_path,
    temp_file,
    truncate=False
  )

  smb_conn.deleteFiles(share_name, fullpath) 

  logger.info(f"Moved file; '{fullpath}' , to back up")


def smb_get_all_csv(hospital: str, model_server_config, timeout: int=5 ) -> List[pd.DataFrame]:
  """
  Retrieves file contents of all files presented as pandas DataFrames, for each
  file in a specific hospitals directory on the Samba Share

  Args:
    hospital: short name for the hospital
    
  Kwargs:
    timeout: how long the connection can be kept alive

  Returns:
    list of pandas.DataFrame objects, containing file contents
  """
  now = datetime.now()

  returnarray = []

  conn = SMBConnection(
    model_server_config.samba_user, 
    model_server_config.samba_pass, 
    model_server_config.samba_pc, 
    model_server_config.samba_name,
  )

  is_connected = conn.connect(model_server_config.samba_ip, timeout=timeout)

  logger.info(f'Samba Connection was succesful: {is_connected}')
  logger.debug(f'/{server_config.samba_Sample}/{hospital}/')

  hospital_sample_folder = f'/{server_config.samba_Sample}/{hospital}/'
  
  logger.debug(f'Searching Share: {model_server_config.samba_share}, at: {hospital_sample_folder}')
  samba_files = conn.listPath(model_server_config.samba_share, hospital_sample_folder)
  logger.debug(f'Got Files:{len(samba_files)}')

  for samba_file in samba_files:
    if samba_file.filename in ['.', '..']:
      continue  
    temp_file = tempfile.NamedTemporaryFile()

    fullpath =  hospital_sample_folder + samba_file.filename
    logger.info(f'Opening File:{samba_file.filename} at {fullpath}')

    conn.retrieveFile(model_server_config.samba_share, fullpath, temp_file)

    temp_file.seek(0)
    try:
      pandas_ds, datestring, protocol = open_csv_file(temp_file)
    except Exception as error_message:
      logger.error(f"Encountered {error_message} at file: {fullpath}")
      temp_file.close()
      continue

    # File Cleanup
    logger.debug(datestring)
    logger.debug(protocol)

    correct_filename = (datestring + protocol + '.csv').replace(' ', '').replace(':','').replace('-','').replace('+','')

    if not samba_file.filename == correct_filename and not samba_file.isReadOnly:
      #Rename
      logger.info(f'Attempting to Rename {hospital_sample_folder + samba_file.filename} into {hospital_sample_folder + correct_filename}')
      try:
        conn.rename(model_server_config.samba_share, hospital_sample_folder + samba_file.filename, hospital_sample_folder + correct_filename)
        logger.info(f'succesfully moved {hospital_sample_folder + samba_file.filename} into {hospital_sample_folder + correct_filename}')
      except: 
        conn.deleteFiles(model_server_config.samba_share, hospital_sample_folder + samba_file.filename)
        logger.info(f'Deleted File: {hospital_sample_folder + samba_file.filename}')

    dt_examination = datetime.strptime(datestring, '%Y%m%d%H%M%S')
    if (now - dt_examination).days > 0:
      logger.debug(f'Moving File {hospital_sample_folder+correct_filename} to backup')
      move_to_backup(conn,temp_file, hospital, hospital_sample_folder + correct_filename, correct_filename, model_server_config)
    else:
      returnarray.append(pandas_ds)
      
    temp_file.close()

  conn.close()
  
  # Sort based on date and time
  sorted_array = sorted(returnarray, key=lambda x: x['Measurement date & time'][0], reverse=True)

  return sorted_array


def get_backup_file(
    date: Union[datetime, date], 
    hospital: str, 
    model_server_config,
    timeout: int=30,
  ) -> List[pd.DataFrame]:
  """
  Retreives a backup file from the Samba Share

  Args:
    date: datetime or date object, used to query for backup files with
    hospital: short_name of hospital to specify which directory to get files from
  
  Kwargs:
    timeout: how long the connection can be kept alive

  Returns:
    list of pandas.DataFrame objects, containing file contents
  """
  # Format date
  date_str = date.strftime('%Y%m%d')
  date_str_len = len(date_str)

  # Establish Samba Share connection
  conn = SMBConnection(
    model_server_config.samba_user, 
    model_server_config.samba_pass, 
    model_server_config.samba_pc, 
    model_server_config.samba_name
  )

  conn.connect(model_server_config.samba_ip)

  # Check if each file in hospital sub directory has the specified date
  # if it does append the file contents as a pandas.DataFrame to the return list
  share_name = model_server_config.samba_share
  backup_folder = f"/{server_config.samba_backup}/{hospital}"
  samba_files = conn.listPath(share_name, backup_folder)
  
  logger.debug(f'Looking for files in samba share folder: {backup_folder}')
  logger.debug(f'Found samba_files: f{samba_files}')

  file_contents = [ ]

  for samba_file in samba_files:
    curr_filename = samba_file.filename
    logger.debug(f'Processing samba file: {curr_filename}')

    if date_str == curr_filename[:date_str_len]:
      temp_file = tempfile.NamedTemporaryFile()

      fullpath = f"{backup_folder}/{curr_filename}"
      
      try:
        conn.retrieveFile(share_name, fullpath, temp_file, timeout=timeout)
        logger.debug(f'Successfully retrieved file')
      except OperationFailure: # File couldn't be found, skip it
        logger.debug(f'Failed to find file: {curr_filename}, skipping file.')
        temp_file.close()
        continue

      temp_file.seek(0)
      try:
        df, _, _ = open_csv_file(temp_file)
        file_contents.append(df)
      except ParserError:
        temp_file.close()
        continue

      temp_file.close()
    else:
      logger.debug(f"first {date_str_len} chars of filename does not match date: '{date_str}'. Skipping file.")

    logger.debug(f'Done processing samba file: {curr_filename}')

  conn.close()

  return file_contents


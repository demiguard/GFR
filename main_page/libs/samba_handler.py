import glob
import os
from pathlib import Path
from datetime import datetime, date
from typing import Tuple
import tempfile
from tempfile import NamedTemporaryFile
import logging
import chardet
import pandas as pd
from pandas.errors import ParserError
from typing import List, Union

from . import server_config
from . import formatting


from main_page import log_util

logger = log_util.get_logger(__name__)

def valid_dataset(pandas_ds):
  if 'Measurement date & time' not in pandas_ds.columns:
    return False
  if 'Pos' not in pandas_ds.columns:
    return False
  if 'Tc-99m CPM' not in pandas_ds.columns:
    return False
  if 'Rack' not in pandas_ds.columns:
    return False

  return True


def open_csv_file_local(file_path: Path) -> Tuple[pd.DataFrame, str, str]:
  """
  Opens a CSV file

  Args:
    temp_file an already opened file

  Returns
    pandas File
  """

  with file_path.open('rb') as file:
    sample = file.read(64)

  encoding = (chardet.detect(sample))['encoding']
  encoding = 'latin' if encoding == "undefined" else encoding

  if file.name.endswith('.xlsm') or file.name.endswith('.xlsx'):
    pandas_ds = pd.read_excel(file_path)
    protocol = pandas_ds['Protocol name'][0]
    date_string = pandas_ds['Measurement date & time'][0].replace('-','').replace(' ','').replace(':','')
    return pandas_ds, date_string, protocol


  try:
    pandas_ds = pd.read_csv(file_path, encoding=encoding)
    protocol = pandas_ds['Protocol name'][0]
    date_string = pandas_ds['Measurement date & time'][0].replace('-','').replace(' ','').replace(':','')
  except ParserError:
    # Hidex file
    try:
      pandas_ds = pd.read_csv(file_path, skiprows=[0,1,2,3], encoding=encoding)
      pandas_ds = pandas_ds.rename(
        columns={
          'Time'                    : 'Measurement date & time',
          'Vial'                    : 'Pos',
          'Normalized Tc-99m (CPM)' : 'Tc-99m CPM',
          'Tc-99m (counts)'         : 'Tc-99m Counts'
        }
      )
      protocol = "Tc-99, Clearance"
    except ParserError:
      pandas_ds = pd.read_csv(file_path, sep=';', encoding=encoding)
      protocol = pandas_ds["Protocol name"][0]

    # Because Hidex is in american format, we change the data column to the ONLY CORRECT format
    pandas_ds['Measurement date & time'] = pandas_ds['Measurement date & time'].apply(formatting.convert_american_date_to_reasonable_date_format)

    date_string = pandas_ds['Measurement date & time'][0].replace('-','').replace(' ','').replace(':','')

    #with file_path.open() as file:
    #  protocol = file.readline()

    # Get protocol

    # Hidex might store these as bytes - convert them to str
    #logger.debug(f"Type protocol: {type(protocol)} with value: {protocol}")

    if isinstance(protocol, bytes):
      #logger.debug(f"Converting bytes protocol to string.")
      protocol = protocol.decode()
      protocol = protocol.replace("\n", "")
      protocol = protocol.replace("\r", "")
      protocol = protocol.replace("\"", "")

  return pandas_ds, date_string, protocol

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
    try:
      pandas_ds = pd.read_csv(temp_file.name, skiprows=[0,1,2,3])
      pandas_ds = pandas_ds.rename(
        columns={
          'Time'                    : 'Measurement date & time',
          'Vial'                    : 'Pos',
          'Normalized Tc-99m (CPM)' : 'Tc-99m CPM',
          'Tc-99m (counts)'         : 'Tc-99m Counts'
        }
      )
      protocol = "Tc-99, Clearance"
    except ParserError:
      pandas_ds = pd.read_csv(temp_file.name, sep=';')
      protocol = pandas_ds["Protocol name"][0]

    # Because Hidex is in american format, we change the data column to the ONLY CORRECT format
    pandas_ds['Measurement date & time'] = pandas_ds['Measurement date & time'].apply(formatting.convert_american_date_to_reasonable_date_format)

    datestring = pandas_ds['Measurement date & time'][0].replace('-','').replace(' ','').replace(':','')
    # Get protocol
    temp_file.seek(0)
    protocol = temp_file.readline()

    temp_file.seek(0)

    # Hidex might store these as bytes - convert them to str
    #logger.debug(f"Type protocol: {type(protocol)} with value: {protocol}")

    if isinstance(protocol, bytes):
      #logger.debug(f"Converting bytes protocol to string.")
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
    pass
    #logger.debug("Samba Info: Failed to create directory '/backup'")

  try:
    smb_conn.createDirectory(share_name, f'backup/{hospital}'.encode())
  except:
    pass
    #logger.debug(f"Samba Info: Failed to create directory '/backup/{hospital}'")

  try:
    smb_conn.storeFileFromOffset(
      share_name,
      store_path,
      temp_file,
      truncate=False
    )
  except:
    logger.warn(f'Samba Info: File already exists at path: {store_path}')

  smb_conn.deleteFiles(share_name, fullpath)

  #logger.info(f"Moved file; '{fullpath}' , to back up")

def get_backup_file(
  date: Union[datetime, date],
  hospital: str,
  model_server_config,
  timeout: int=30) -> List[pd.DataFrame]:
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

  return_array = []

  date_str = date.strftime('%Y%m%d')
  date_str_len = len(date_str)
  backup_dir = Path(f'/media/samba/{server_config.samba_backup}/{hospital}')

  for path in backup_dir.glob(f'{date_str}*'):
    df, _, _ = open_csv_file_local(path)
    return_array.append(df)

  return return_array

def smb_get_all_csv(hospital:str, model_server_config, timeout: int = 60):
  sample_dir = Path(f'/media/samba/{server_config.samba_Sample}/{hospital}')
  backup_dir = Path(f'/media/samba/{server_config.samba_backup}/{hospital}')

  return_array = []
  error_messages = []

  now = datetime.now()
  for path in sample_dir.glob("*"):
    if not path.is_file():
      continue

    try:
      pandas_ds, datestring, protocol = open_csv_file_local(path)
    except Exception as E:
      logger.error(f"Encountered {E} at file: {path}")
      continue

    correct_filename = (datestring + protocol + '.csv').replace(' ', '').replace(':','').replace('-','').replace('+','')
    if path.name != correct_filename:
      target_path = sample_dir / correct_filename
      logger.info(f"moving {path} to {target_path}")
      path = path.rename(target_path)

    dt_examination = datetime.strptime(datestring, '%Y%m%d%H%M%S')
    if valid_dataset(pandas_ds):
      if (now - dt_examination).days > 0:
        backup_path = backup_dir / correct_filename
        logger.info(f"moving {path} to {backup_path}")
        path = path.rename(backup_path)
      else:
        return_array.append(pandas_ds)
    else:
      error_messages.append(f"Der er ukendt tælling. Check om det Wizarden er konfiguret til Tc-99")

  sorted_array = sorted(return_array, key=lambda x: x['Measurement date & time'][0], reverse=True)

  return sorted_array, error_messages

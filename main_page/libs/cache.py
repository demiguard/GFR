#Python packages
import shutil
import glob
from typing import Union, Type, List
from pathlib import Path

#Custom modules
from . import dicomlib
from . import server_config 
from .query_wrappers import pacs_query_wrapper

from main_page import log_util

logger = log_util.get_logger(__name__)
"""
  This file is responsible for maintaining all actions in regarding the search cache

  Cache file structure is the same:
  
    search_cache/{Accession_number_1}/{Accession_number_1}.dcm
    Historic studies to {Accesstion_number_1} are stores as:
    search_cache/{Accession_number_1}/{Accession_number_2}.dcm
  
  Historic Studies are not gathered when the server retrieves an old study

"""

def move_file_to_cache(filepath, accession_number: str, overwrite=True):
  """
    Moves a local file or dicom directory to the cache. If the path is to a file, it creates the nessary infastructure to maintain status quo

    Args:
      filepath - The current location of the file
      Accession number - The accession of the file
    Kwargs:
      Overwrite: if False this will return false if the function would overwrite an existing file
    Returns:
      Move_status: Bool, Reports the success of the move

  """
  if type(filepath) == str: filepath = Path(filepath)

  if not(filepath.exists()):
    logger.error(f'File: {filepath} does not exists')
    return False
  
  target_dir = Path(server_config.SEARCH_CACHE_DIR,accession_number) 
  target = Path(server_config.SEARCH_CACHE_DIR,accession_number,f'{accession_number}.dcm')
  if target.exists():
    if not(overwrite):
      logger.error(f'File {str(target)} exists, no action taken')
      return False
    logger.error(f'Overwritting file at: {str(target)}')
    shutil.rmtree(target_dir)
  
  #This is the directory that will contain the cached files
  #If the think is a dir or not
  if filepath.is_dir():
    shutil.move(filepath, target_dir)
  else:
    #Target is a path to a file 
    target_dir.mkdir()
    shutil.move(filepath, target)
  
  return True


def retrieve_file_from_cache(user,accession_number: str, ask_pacs=True):
  """
    Retrieves a file from the cache, if the file is unavailble then file is retrieve from 

    Args:
      user: Django user with access to send to pacs
      accession_number:  The accession of the wished study
    KWargs:
      ask_pacs: Bool - If True: makes a query for pacs for the requested study
    Returns:
      Pydicom Dataset or None - The request dataset or none if does not exists

  """
  target = Path(server_config.SEARCH_CACHE_DIR, accession_number, f'{accession_number}.dcm')

  if target.exists():
    return dicomlib.dcmread_wrapper(target)
  elif not(ask_pacs):
    return None

  dataset, path_to_dataset = pacs_query_wrapper.get_study(user, accession_number)

  if path_to_dataset == "Error":
    return None
  move_file_to_cache(path_to_dataset, accession_number)

  return dataset


def get_all_cache_studies():
  studies_dirs = glob.glob(f'{server_config.SEARCH_CACHE_DIR}/*')
  accession_numbers = [ study_dir.split('/')[-1] for study_dir in studies_dirs]
  # Just be happy i didn't put a list comprehention in my list comprehention
  return [ dicomlib.dcmread_wrapper(Path(server_config.SEARCH_CACHE_DIR, accession_number, f'{accession_number}.dcm')) for accession_number in accession_numbers]

  
def clean_cache(life_time: int):
    """
      This function should be called once per day, to clean up the cache to ensure GFR is complient with GDPR

      Args:
        life-time - The amount of days that studies may life in the cache
    """
    studies = get_all_cache_studies()
    for study in studies:
      study_datetime = datetime.datetime.strptime(dicomlib.get_study_date(study), "%Y%m%d")
      time_diff = now - study_datetime
      if time_diff.days > life_time:
        #This study is too old and should be deleted!
        target_path = Path(server_config.SEARCH_CACHE_DIR, study.AccessionNumber)
        shutil.rmtree(target_path)

def move_file_from_cache_active_studies(accession_number : str, target_path, move_dir=True ):
  """
    This function moves a file in the cache to another destination. This removes the file from the cache
    To ensure that a file exists use the function file in cache

    Args:
      accession_number : str the wished study, the study must be in the cache
      target_path      : str or Path-object, where the file is moved to, parent path must exists and this function cannot overwrite
    Raises:
      FileNotFoundError : Raised if the target parent directory does not exists. 
      FileExistsError   : Raised if the target already exists premovement
  """
  #Init
  if not(isinstance(target_path, Path)):
    target_path = Path(target_path)

  study_dir = Path(server_config.SEARCH_CACHE_DIR, accession_number)
  #Checking if all paths exists for file transfer
  if not(target_path.parent.exists()):
    raise FileNotFoundError('Parent directory for file does not exists')
  if not(study_dir.exists()):
    raise FileNotFoundError("Study is not in the cache")
  if target_path.exists():
    raise FileExistsError(f"{str(target_path)} exists")

  #Moving the file
  if move_dir:
    shutil.move(study_dir, target_path)
  else:
    study_path = Path(study_dir, f'{accession_number}.dcm')
    shutil.move(study_path, target_path)
    shutil.rmtree(study_dir)


def file_in_cache(accession_number):
  return Path(server_config.SEARCH_CACHE_DIR, accession_number).exists()

  


  
import json
from os import environ
from pathlib import Path
from typing import Any, Dict

default_environ = {
  'GFR_LOG_PATH' : '/home/cjen0668/work/gfr/log/gfr.log',
  'RIS_THREAD_LOG_PATH' : '/home/cjen0668/work/gfr/ris_thread.log',
  'GFR_CONTROL_STUDY_PATH' : '/home/cjen0668/work/gfr/control_studies',
  'GFR_DELETE_PATH' : '/home/cjen0668/work/gfr/deleted_studies',
  'GFR_FIND_RESPONSE_PATH' : '/home/cjen0668/work/gfr/active_dicom_objects',
  'GFR_SEARCH_CACHE_PATH' : '/home/cjen0668/work/gfr/search_cache',
  'GFR_SEARCH_PATH' : '/home/cjen0668/work/gfr/search_dir',
  'GFR_STATIC_PATH' : '/home/cjen0668/work/gfr/main_page/static/main_page/',
  'GFR_DATABASE_NAME' : 'gfr',
  'GFR_DATABASE_USER' : 'gfr',
  'GFR_DATABASE_PW' : 'gfr',
  'GFR_DATABASE_HOST' : 'localhost',
}


def load_config():
  config_file_path = Path('clairvoyance_config.json')

  if not config_file_path.exists() and config_file_path.is_file():
    return None

  with config_file_path.open() as config_file:
    config = json.load(config_file)
  return config

config_file: Dict[str, Any] = load_config()

def get_config(key: str) -> str:
  if config_file is not None and key in config_file:
    return config_file[key]
  if key in environ:
    return environ[key]
  if key in default_environ:
    return environ[key]
  raise KeyError

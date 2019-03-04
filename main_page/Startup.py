import os

from .libs import server_config


def init_dicom_env():
  """
  Sets the DCMDICTPATH if not already set
  """
  try:
    if not os.environ['DCMDICTPATH']:
      os.environ['DCMDICTPATH'] = server_config.DCMDICTPATH
  except KeyError:
    os.environ['DCMDICTPATH'] = server_config.DCMDICTPATH


def start_up():
  """
  The main start up function which calls aditional start up functions for other
  components
  """
  init_dicom_env()

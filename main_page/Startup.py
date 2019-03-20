import datetime, logging, os 
import platform


from .libs import server_config

def init_logger():
  pass
  


def init_dicom_env():
  """
  Sets the DCMDICTPATH if not already set
  """
  os_name = platform.platform().lower()
  if 'ubuntu' in os_name:
    dcmdictpath = server_config.DICOMDICT_UBUNTU
  elif 'centos' in os_name:
    dcmdictpath = server_config.DICOMDICT_CENTOS

  if not 'DCMDICTPATH' in os.environ:
    os.environ['DCMDICTPATH'] = dcmdictpath


def start_up():
  """
  The main start up function which calls aditional start up functions for other
  components
  """
  init_dicom_env()
  init_logger()
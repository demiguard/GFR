import datetime, logging, os 
import platform

from .libs import server_config
from .libs.query_wrappers import pacs_query_wrapper as pacs


def init_logger():  
  logfile = server_config.LOG_DIR + 'logging_file_' + str(datetime.date.today()).replace(' ','').replace('.','') + '.log'

  if not os.path.exists(server_config.LOG_DIR):
    os.mkdir(server_config.LOG_DIR)

  logging.basicConfig(filename=logfile, level=server_config.LOG_LEVEL, format='%(asctime)s (%(filename)s/%(funcName)s) - [%(levelname)s] : %(message)s')


def init_dicom_env():
  """
  Sets the DCMDICTPATH if not already set
  """
  logging.getLogger()

  os_name = platform.platform().lower()
  if 'ubuntu' in os_name:
    dcmdictpath = server_config.DICOMDICT_UBUNTU
  elif 'centos' in os_name:
    dcmdictpath = server_config.DICOMDICT_CENTOS

  if not 'DCMDICTPATH' in os.environ:
    os.environ['DCMDICTPATH'] = dcmdictpath

  logging.debug('DICOM envoriment variable set to: {0}'.format(dcmdictpath))


def start_up():
  """
  The main start up function which calls aditional start up functions for other
  components
  """
  init_logger()
  init_dicom_env()
  #pacs.start_scp_server()
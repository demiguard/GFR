import datetime
import logging 

from main_page.libs.dirmanager import try_mkdir
from .libs import server_config

global ris_thread


def init_logger():  
  logfile = server_config.LOG_DIR + 'logging_file_' + str(datetime.date.today()).replace(' ','').replace('.','') + '.log'

  try_mkdir(server_config.LOG_DIR)

  logging.basicConfig(filename=logfile, level=server_config.LOG_LEVEL, format='%(asctime)s (%(filename)s/%(funcName)s) - [%(levelname)s] : %(message)s')
import datetime
import logging
import re

from pathlib import Path
from main_page.libs.dirmanager import try_mkdir
from .libs import server_config

global ris_thread


def init_logger():
  log_filepath = Path(server_config.LOG_DIR, server_config.LOG_FILENAME)

  try_mkdir(server_config.LOG_DIR)

  logger = logging.getLogger()
  log_format = "%(asctime)s (%(filename)s/%(funcName)s) - [%(levelname)s] : %(message)s"
  handler = logging.handlers.TimedRotatingFileHandler(
    log_filepath, 
    when="midnight", 
    interval=1
  )

  handler.setLevel(server_config.LOG_LEVEL)
  formatter = logging.Formatter(log_format)
  handler.setFormatter(formatter)
  handler.suffix = "%Y-%m-%d"
  handler.extMatch = re.compile(r"^\d{8}$") 
  logger.addHandler(handler)
  
  # Django-auth-ldap logging for debugging connection to ApacheDS LDAP server
  # This logger setup will output debugging information to the console and
  # not the main GFR logging file
  ldap_logger = logging.getLogger('django_auth_ldap')
  ldap_logger.addHandler(logging.StreamHandler())
  ldap_logger.setLevel(logging.DEBUG)

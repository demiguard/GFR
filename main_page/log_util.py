import datetime
import logging
import re

from pathlib import Path
from main_page.libs.dirmanager import try_mkdir
from .libs import server_config

"""
### WARNING ###
This logging utility was created as to resolve potential issues related to
having multiple loggers in different threads. Please refrain from editting
this module and it's functions as it will effect logging in all other modules!
"""

def get_logger(
  name,
  log_filename=server_config.LOG_FILENAME,
  log_level=server_config.LOG_LEVEL
  ):
  """
  Creates a new logger

  Args:
    name: name of the logger (generally this should just be called with __name__)

  Kwargs:
    log_filename: filename of file to log to in main_page/log/
    log_level: logging level to use for the logger

  Remark:
    Allow for logging to multiple files without overlap.
  """
  log_filepath = Path(server_config.LOG_DIR, log_filename)

  try_mkdir(server_config.LOG_DIR)

  logger = logging.getLogger(name) # Get the root logger
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

  # Set the root logging level - required for child loggers to have this or
  # higher effective log level
  logger.setLevel(server_config.LOG_LEVEL)

  return logger

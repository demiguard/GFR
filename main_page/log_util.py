import datetime
import logging
import re

from pathlib import Path
from main_page.libs.dirmanager import try_mkdir
from .libs import server_config


def get_logger(
  name, 
  log_filename=server_config.LOG_FILENAME, 
  log_level=server_config.LOG_LEVEL
  ):
  """

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

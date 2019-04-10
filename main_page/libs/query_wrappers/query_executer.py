from subprocess import check_output, CalledProcessError
import logging


logger = logging.getLogger()

def execute_query(cmd):
  """
  Executes a query comamnd
  
  Args:
    cmd: command query to execute given as a list of strings

  Return:
    Output from the ran command, None if command returned non zero exit-code
  """
  logger.info('Query to execute: {0}'.format(' '.join(cmd)))

  try:
    return check_output(cmd)
  except (CalledProcessError, FileNotFoundError):
    return None
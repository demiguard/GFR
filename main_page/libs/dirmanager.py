import os

def check_and_create(dirname):
  """
  checks if a directory exists, if not it creates it


  """
  if not os.path.exists(dirname):
    os.mkdir(dirname) 

def check_combined_and_create(*argv):
  """
  Recursivly Checks if a directory exists, if it doesn't it creates directory s.t.
  after the function call you have a structure:
  '.arg1/arg2/arg3/../argN/'

  Args:
    argv : String - None empty

  Note: if string is empty it will simply skip over the arg

  """
  basestring = ''
  for arg in argv:
    basestring += arg + '/'
    check_and_create(basestring)

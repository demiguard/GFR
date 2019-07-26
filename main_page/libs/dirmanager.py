import os


def __try_mkdir(dirpath: str) -> None:
  """
  Checks if a directory exists, if not it creates it

  Args:
    dirpath: path of directory to try and create
  """
  if not os.path.exists(dirpath):
    os.mkdir(dirpath)


def try_mkdir(dirpath: str, mk_parents: bool=False) -> None:
  """
  Checks if a directory exists, if not it creates it

  Args:
    dirpath: path of directory to try and create

  Kwargs:
    mk_parents: if True will create all parent directories of the dirpath,
                before trying to create the dirpath directory
  """
  if mk_parents:
    # Remove any empty directories and dots
    dir_split = list(filter(lambda x: x, dirpath.split('/')))

    base_path = ''
    for parent_dir in dir_split:
      base_path += f"{parent_dir}/"
      __try_mkdir(base_path)
  else:
    __try_mkdir(dirpath)

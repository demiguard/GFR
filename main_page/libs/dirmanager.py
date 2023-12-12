import os
from pathlib import Path
from typing import Union

def try_mkdir(dirPath: Union[str, Path], mk_parents: bool=False) -> None:
  if isinstance(dirPath, str):
    dirPath = Path(dirPath)

  dirPath.mkdir(parents=mk_parents)

import os
import tarfile
from datetime import date
from typing import Union

def create_backup( 
    path: Union[str, os.PathLike[str]], *,
    dir: Union[str, os.PathLike[str], None] = None
) -> str:
    """ Create gzipped tar file of `path`. 
    
    Parameters
    ----------
    path
        Path to file or directory to back up.
    dir 
        Directory which tar file is created on.

    Returns
    -------
    str 
        Path of created tar file
    
    Raises
    ------
    FileNotFoundError
        If "path" or/and "dir" could not be found.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f'{path} not found')
    if dir and not os.path.exists(dir):
        raise FileNotFoundError(f'{dir} not found')
    date_str: str = date.today().strftime("%Y%m%d")
    base_name: str = f'{os.path.basename(path)}-{date_str}.tar.gz'
    if dir is None:
        save_name: str = base_name
    else:
        save_name = os.path.join(dir, base_name)
    with tarfile.open(save_name, mode='w:gz') as tar:
        tar.add(path)
    return save_name
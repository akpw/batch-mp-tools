## Copyright (c) 2014 Arseniy Kuznetsov
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

""" Utility functions for use in ffmp module
"""

import os, shutil, tempfile, subprocess, shlex
import copyreg, types, time, datetime
from functools import wraps
from contextlib import contextmanager


class FFmpegNotInstalled(Exception):
    pass
class CmdProcessingError(Exception):
    pass
class FFmpegArgsError(Exception):
    pass

# A subset of common media formats supported by FFmpeg
# run <ffmpeg -formats> for full list
SUPPORTED_MEDIA =  ('.aif', '.m4a', '.mp3',
                    '.wma', '.avi', '.flv', '.m4v',
                    '.mov', '.mp4', '.mpg', '.wmv', '.mkv')
BACKUP_DIR_PREFIX = '_origs_'

@contextmanager
def temp_dir():
    """ Temp dir context manager
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        yield tmp_dir
    finally:
        # remove tmp dir
        shutil.rmtree(tmp_dir)

def timed(f):
    """ A simple timing decorator
    """
    @wraps(f)
    def wrapper(*args, **kwds):
        start = time.time()
        result = f(*args, **kwds)
        elapsed = time.time() - start
        return (result, elapsed)
    return wrapper

@timed
def run_cmd(cmd):
    ''' Runs command in a separate process
    '''
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.communicate()[0].decode('utf-8')
    if proc.returncode != 0:
        raise CmdProcessingError(output)
    return output

def ffmpeg_installed():
    """ Checks if ffmpeg is installed
        P.S.
            Not likely to work well for Windows. Rather needs to use smth like
            winreq module (https://docs.python.org/2/library/_winreg.html)
            for checking the registry:
                HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\\Uninstall
            .. or smth along these lines :)
    """
    ffmpeg_app_name = 'ffmpeg' if os.name != 'nt' else 'ffmpeg.exe'
    for path in os.environ['PATH'].split(os.pathsep):
        app_path = os.path.join(path, ffmpeg_app_name)
        if os.path.isfile(app_path) and os.access(app_path, os.X_OK):
            return True
    return False

def get_media_files(src_dir=os.curdir, recursive = False):
    """Gets all media files from source directory and (if recursive) its subdirectories
    """
    if recursive:
        fpathes = [os.path.join(r,f) for r,d,files in os.walk(src_dir)
                            for f in files if f.endswith(SUPPORTED_MEDIA)]
    else:
        fpathes = (os.path.join(src_dir, fname) for fname in os.listdir(src_dir)
                                                if fname.endswith(SUPPORTED_MEDIA))
        fpathes = [f for f in fpathes if os.path.isfile(f)]

    return fpathes

def setup_backup_dirs(files):
    """ Given list of files pathes,
        creates backup dirs in respective folder(s)
    """
    backup_dir = '{0}{1}'.format(BACKUP_DIR_PREFIX, datetime.datetime.now().strftime("%y%b%d_%H%M%S"))
    backup_dirs = []
    for file in files:
        fdir, fname = os.path.split(file)
        if os.access(fdir, os.X_OK):
            backup_path = os.path.join(fdir, backup_dir)
            if not os.path.exists(backup_path):
                os.mkdir(backup_path)
            backup_dirs.append(backup_path)
    return backup_dirs

def get_backup_dirs(src_dir, recursive = False):
    """ Gets all backup directories from from source folder and (if recursive) its subdfolders
    """
    if recursive:
        dir_names = [os.path.join(r,d) for r,dirs,files in os.walk(src_dir)
                            for d in dirs if d.find(BACKUP_DIR_PREFIX) >= 0]
    else:
        dir_names = (os.path.join(src_dir, fname) for fname in os.listdir(src_dir)
                                                if fname.find(BACKUP_DIR_PREFIX) >= 0)
        dir_names = [dir for dir in dir_names if os.path.isdir(dir)]

    return dir_names

"""
    Python multiprocessing pickles stuff, and bound methods are not yet picklable
    These methods serve as a workaround, more at:
    http://bytes.com/topic/python/answers/552476-why-cant-you-pickle-instancemethods#edit2155350
"""
def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class

    if func_name.startswith('__') and not func_name.endswith('__'):
        cls_name = cls.__name__.lstrip('_')
        if cls_name:
            func_name = '_' + cls_name + func_name

    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)

copyreg.pickle(types.MethodType, _pickle_method, _unpickle_method)


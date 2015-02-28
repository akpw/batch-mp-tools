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

''' FFmpeg-related utilities
'''

import os, subprocess, shlex, sys
import time, datetime, json
from functools import wraps
from collections import namedtuple
import batchmp.fstools.fsutils as fsutils


class FFmpegNotInstalled(Exception):
    pass
class CmdProcessingError(Exception):
    pass


class FFH:
    BACKUP_DIR_PREFIX = '_backup_'
    FFEntry = namedtuple('FFEntry', ['path', 'format', 'audio', 'artwork'])

    @staticmethod
    def ffmpeg_installed():
        """ Checks if ffmpeg is installed
            P.S. / TBD
                Not likely to work well for Windows. Rather needs to use smth like
                winreq module (https://docs.python.org/2/library/_winreg.html)
                for checking the registry:
                    HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\\Uninstall
                .. or smth along these lines
        """
        ffmpeg_app_name = 'ffmpeg' if os.name != 'nt' else 'ffmpeg.exe'
        for path in os.environ['PATH'].split(os.pathsep):
            app_path = os.path.join(path, ffmpeg_app_name)
            if os.path.isfile(app_path) and os.access(app_path, os.X_OK):
                return True
        return False

    @staticmethod
    def media_file_info(fpath):
        if not FFH.ffmpeg_installed():
            return None

        cmd = ''.join(('ffprobe ',
                            ' -v quiet',
                            ' -show_streams',
                            #' -select_streams a',
                            ' -show_format',
                            ' -print_format json',
                            ' "{}"'.format(fpath)))
        try:
            output, _ = run_cmd(cmd)
        except CmdProcessingError as e:
            return None
        else:
            format = json.loads(output).get('format')

            streams = json.loads(output)['streams']
            audio_stream = {k:v for dict in streams
                                    for k,v in dict.items()
                                        if 'codec_type' in dict and
                                            dict['codec_type'] == 'audio'}
            if not audio_stream:
                return None
            artwork_stream = {k:v for dict in streams
                                    for k,v in dict.items()
                                        if 'codec_type' in dict and dict['codec_type'] == 'video'
                                            and dict['codec_name'] in ('jpeg', 'png', 'gif', 'tiff', 'bmp', 'mjpeg')}
            return FFH.FFEntry(fpath, format, audio_stream, artwork_stream)

    @staticmethod
    def supported_media(fpath):
        if not FFH.media_file_info(fpath):
            return False
        else:
            return True

    @staticmethod
    def media_files(src_dir,
                    start_level = 0, end_level = sys.maxsize,
                    include = '*', exclude = '', sort = 'n',
                    filter_dirs = True, filter_files = True):
        """ yields media files supported by FFmpeg
        """
        pass_filter = lambda fpath: FFH.supported_media(fpath)
        return fsutils.DWalker.file_entries(src_dir,
                                            start_level = start_level, end_level = end_level,
                                            include = include, exclude = exclude, sort = sort,
                                            filter_dirs = True, filter_files = True,
                                            pass_filter = pass_filter)

    @staticmethod
    def setup_backup_dirs(fpathes):
        """ Given list of files pathes,
            creates backup dirs in respective folder(s)
        """
        backup_dir = '{0}{1}'.format(FFH.BACKUP_DIR_PREFIX,
                                        datetime.datetime.now().strftime("%y%b%d_%H%M%S"))
        backup_dirs = []
        for fpath in fpathes:
            fdir = os.path.dirname(fpath)
            if os.access(fdir, os.X_OK):
                backup_path = os.path.join(fdir, backup_dir)
                if not os.path.exists(backup_path):
                    os.mkdir(backup_path)
                backup_dirs.append(backup_path)
        return backup_dirs

    @staticmethod
    def backup_dirs(src_dir, recursive = True):
        """ list of  backup directories from from source folder and (if recursive) its subdfolders
        """
        if recursive:
            dir_names = [os.path.join(r,d) for r,dirs,files in os.walk(src_dir)
                                for d in dirs if d.find(FFH.BACKUP_DIR_PREFIX) >= 0]
        else:
            dir_names = (os.path.join(src_dir, fname) for fname in os.listdir(src_dir)
                                                    if fname.find(FFH.BACKUP_DIR_PREFIX) >= 0)
            dir_names = [dir for dir in dir_names if os.path.isdir(dir)]
        return dir_names


# general-level utility functions
def timed(f):
    """ A timing decorator
    """
    @wraps(f)
    def wrapper(*args, **kwds):
        start = time.time()
        result = f(*args, **kwds)
        elapsed = time.time() - start
        return (result, elapsed)
    return wrapper

@timed
def run_cmd(cmd, shell = False):
    ''' Runs shell command in a separate process
    '''
    if not shell:
        cmd = shlex.split(cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell = shell)
    output = proc.communicate()[0].decode('utf-8')
    if proc.returncode != 0:
        raise CmdProcessingError(output)
    return output


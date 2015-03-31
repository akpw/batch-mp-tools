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


import sys, datetime, math
from batchmp.ffmptools.ffutils import FFH, timed, FFmpegNotInstalled
from abc import ABCMeta, abstractmethod


class FFMPRunner(metaclass = ABCMeta):
    ''' Base FFMPRunner
    '''
    def __init__(self):
        if not FFH.ffmpeg_installed():
            raise FFmpegNotInstalled

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def run_report(self, cpu_core_time, total_elapsed):
        ''' Info summary on executed FFMP commands
        '''
        ttd = datetime.timedelta(seconds = math.ceil(total_elapsed*100)/100)
        ctd = datetime.timedelta(seconds = math.ceil(cpu_core_time*100)/100)

        print('Total running time: {}'.format(str(ttd).rstrip('0')))
        print('Cumulative FFmpeg CPU Cores time: {}'.format(str(ctd).rstrip('0')))

    # Internal helpers
    def _prepare_files(self, src_dir, *,  end_level = sys.maxsize, sort = None,
                         include = None, exclude = None, filter_dirs = True, filter_files = True,
                         backup = True, pass_filter = None):

        media_files = [fpath for fpath in FFH.media_files(src_dir,
                                        end_level = end_level, sort = sort,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        pass_filter = pass_filter)]

        # if backup is required, prepare the backup dirs
        if backup:
            backup_dirs = FFH.setup_backup_dirs(media_files)
        else:
            # just build a sequence of None-s
            backup_dirs = [None for bd in media_files]

        return media_files, backup_dirs

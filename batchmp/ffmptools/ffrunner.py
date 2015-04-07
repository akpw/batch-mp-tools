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


import os, sys, datetime, math
from abc import ABCMeta, abstractmethod
from batchmp.commons.taskprocessor import Task
from batchmp.ffmptools.ffutils import FFH, FFmpegNotInstalled
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.tagsholder import TagHolder
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands, FFmpegBitMaskOptions


class FFMPRunnerTask(Task):
    ''' Represents an abstract FFMP Runner task
    '''
    def __init__(self, fpath, target_dir, ff_global_options, ff_other_options, preserve_metadata):
        self.fpath = fpath
        self.target_dir = target_dir
        self.tag_holder = TagHolder() if preserve_metadata else None

        self.cmd = ''.join((self._ffmpeg_input(fpath),
                            FFmpegBitMaskOptions.ff_global_options(ff_global_options),
                            ' {}'.format(ff_other_options) if ff_other_options else ''))
    #Helpers
    def _ffmpeg_input(self, fpath):
        if fpath is not None:
            return ''.join(('ffmpeg',
                                FFmpegCommands.LOG_LEVEL_ERROR,
                                ' -i "{}"'.format(fpath)))
        return ''

    def _store_tags(self):
        if self.tag_holder:
            handler = MutagenTagHandler() + FFmpegTagHandler()
            if handler.can_handle(self.fpath):
                self.tag_holder.copy_tags(handler.tag_holder)

    def _restore_tags(self, fpath):
        if self.tag_holder:
            handler = MutagenTagHandler() + FFmpegTagHandler()
            if handler.can_handle(fpath):
                handler.tag_holder.copy_tags(self.tag_holder)
                handler.save()

    def _FF_preserve_quality(self):
        # try to explicitly tell FFMpeg to preserve the original quality
        fname_ext = os.path.splitext(self.fpath)[1].strip().lower()
        if fname_ext == '.flac':
            self.cmd = ''.join((self.cmd, ' {}'.format(FFmpegCommands.CONVERT_LOSSLESS_FLAC)))
        elif fname_ext == '.m4a':
            self.cmd = ''.join((self.cmd, ' {}'.format(FFmpegCommands.CONVERT_LOSSLESS_ALAC)))
        else:
            self.cmd = ''.join((self.cmd, ' {}'.format(FFmpegCommands.CONVERT_COPY_VBR_QUALITY)))


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


    ## Internal helpers
    @staticmethod
    def _prepare_files(src_dir, *,
                        end_level = sys.maxsize,
                        include = None, exclude = None,
                        filter_dirs = True, filter_files = True,
                        target_dir = None, target_dir_prefix = None,
                        pass_filter = None):
        ''' Builds a list of matching media files to process,
            along with their respective target out dirs
        '''
        media_files = [fpath for fpath in FFH.media_files(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        pass_filter = pass_filter)]

        target_dirs = FFMPRunner._setup_target_dirs(src_dir = src_dir,
                                                target_dir = target_dir, target_dir_prefix = target_dir_prefix,
                                                fpathes = media_files)

        return media_files, target_dirs

    @staticmethod
    def _setup_target_dirs(src_dir, *,
                            target_dir = None, target_dir_prefix = None,
                            fpathes = None):
        DEFAULT_TARGET_DIR_PREFIX = 'processed'
        if target_dir_prefix is None:
            target_dir_prefix = DEFAULT_TARGET_DIR_PREFIX
        target_dir_name = '{0}_{1}_{2}'.format(os.path.basename(src_dir),
                                                target_dir_prefix,
                                                datetime.datetime.now().strftime("%y%b%d_%H%M%S"))
        if target_dir is None:
            target_dir = os.path.join(os.path.dirname(src_dir), target_dir_name)
        else:
            target_dir = os.path.join(target_dir, target_dir_name)

        # target dirs
        target_dirs = []
        for fpath in fpathes:
            relpath = os.path.relpath(os.path.dirname(fpath), src_dir)
            if relpath.startswith(os.pardir):
                raise ValueError('File not in specified source directory or its subfolders')
            elif relpath.endswith('{}'.format(os.path.curdir)):
                relpath = relpath[:-1]

            target_path = os.path.join(target_dir, relpath)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            target_dirs.append(target_path)

        return target_dirs



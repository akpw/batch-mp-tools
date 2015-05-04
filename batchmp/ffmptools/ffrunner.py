# coding=utf8
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


import os, sys, shlex
from enum import IntEnum
from batchmp.commons.utils import MiscHelpers
from batchmp.commons.taskprocessor import Task, TasksProcessor
from batchmp.ffmptools.ffutils import FFH, FFmpegNotInstalled
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.tagsholder import TagHolder
from batchmp.fstools.fsutils import UniqueDirNamesChecker
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands, FFmpegBitMaskOptions


class FFMPRunnerTask(Task):
    ''' Represents an abstract FFMP Runner task
    '''
    def __init__(self, fpath, target_dir, log_level,
                        ff_general_options, ff_other_options, preserve_metadata):
        self.fpath = fpath
        self.target_dir = target_dir
        self.log_level = log_level

        self.ff_general_options = FFmpegBitMaskOptions.ff_general_options(ff_general_options)
        self.ff_other_options = ff_other_options

        self.tag_holder = TagHolder() if preserve_metadata else None

        self._check_defaults()

    @property
    def ff_cmd(self):
        ''' Base FFmpeg command builder
        '''
        return ''.join(('ffmpeg',
                            FFmpegCommands.LOG_LEVEL_ERROR,
                            ' -i {}'.format(shlex.quote(self.fpath)),
                            self.ff_general_options,
                            self.ff_other_options))

    # Helpers
    def _check_defaults(self):
        if not self.ff_other_options:
            self.ff_other_options = FFmpegCommands.CONVERT_COPY_VBR_QUALITY

        if not self.ff_general_options:
            self.ff_general_options = FFmpegBitMaskOptions.ff_general_options(
                                  FFmpegBitMaskOptions.COPY_CODECS | FFmpegBitMaskOptions.MAP_ALL_STREAMS)

            if self.ff_other_options == FFmpegCommands.CONVERT_COPY_VBR_QUALITY:
                self.ff_other_options += self._ff_cmd_exclude_artwork_streams()

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

    def _log(self, msg, type):
        if self.log_level and self.log_level >= type:
            # quick log
            print(msg)

    # FFmpeg command parts builders
    def _ff_cmd_exclude_artwork_streams(self):
        media_entry = FFH.media_file_info_full(self.fpath)
        exclude_artworks_cmd = ''
        if media_entry:
            for artwork_stream in media_entry.artwork_streams:
                idx = artwork_stream.get('index')
                if idx is not None:
                    exclude_artworks_cmd = '{0} {1}'.format(exclude_artworks_cmd,
                                                            FFmpegCommands.exclude_input_stream(idx))
        return exclude_artworks_cmd


class LogLevel(IntEnum):
    QUIET = 0
    FFMPEG = 1
    VERBOSE = 2


class FFMPRunner:
    ''' Base FFMPRunner
    '''
    def __init__(self):
        if not FFH.ffmpeg_installed():
            print(FFmpegNotInstalled().default_message)
            sys.exit(0)

    def run_tasks(self, tasks, msg = None, serial_exec = False, quiet = False):
        if tasks and len(tasks) > 0:
            print('{0} media files to process'.format(len(tasks)) if msg is None else msg)

            (tasks_results, cpu_core_time), total_elapsed = TasksProcessor().process_tasks(tasks,
                                                                            serial_exec = serial_exec,
                                                                            quiet = quiet)
            # print run report
            if not quiet:
                self.run_report(tasks_results, cpu_core_time, total_elapsed)
        else:
            print('No media files to process')


    def run_report(self, tasks_results, cpu_core_time, total_elapsed):
        ''' Info summary on executed FFMP commands
        '''
        succeeded = sum(1 for result in tasks_results if result.succeeded)
        failed = sum(1 for result in tasks_results if not result.succeeded)

        total_elapsed_str = MiscHelpers.time_delta_str(total_elapsed)
        cpu_core_time_str = MiscHelpers.time_delta_str(cpu_core_time)

        num_tasks = len(tasks_results)
        print('Finished running {0} task{1} '\
                        '(Succeeded: {2}, Failed: {3})'.format(num_tasks,
                                                            '' if num_tasks == 1 else 's',
                                                            succeeded, failed))
        print('Cumulative FFmpeg CPU Cores time: {}'.format(cpu_core_time_str))
        print('Total running time: {}'.format(total_elapsed_str))


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
        # check inputs
        # target dir prefix
        DEFAULT_TARGET_DIR_PREFIX = 'processed'
        if target_dir_prefix is None:
            target_dir_prefix = DEFAULT_TARGET_DIR_PREFIX
        # target dir
        if target_dir is None:
            target_dir = os.path.dirname(src_dir)

        # target path (within the target dir)
        target_dir_name = '{0}_{1}'.format(os.path.basename(src_dir), target_dir_prefix)
        target_dir_name = UniqueDirNamesChecker(target_dir).unique_name(target_dir_name)
        target_path_dir = os.path.join(target_dir, target_dir_name)

        # target dirs
        target_dirs = []
        for fpath in fpathes:
            relpath = os.path.relpath(os.path.dirname(fpath), src_dir)
            if relpath.startswith(os.pardir):
                raise ValueError('File not in specified source directory or its subfolders')
            elif relpath.endswith('{}'.format(os.path.curdir)):
                relpath = relpath[:-1]

            target_path = os.path.join(target_path_dir, relpath)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            target_dirs.append(target_path)

        return target_dirs


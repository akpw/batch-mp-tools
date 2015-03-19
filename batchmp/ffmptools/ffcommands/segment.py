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


""" Batch splitting of media files
"""
import shutil, sys, os, datetime, math, fnmatch
from batchmp.fstools.fsutils import temp_dir, UniqueDirNamesChecker
from batchmp.ffmptools.ffrunner import FFMPRunner
from batchmp.ffmptools.taskpp import Task, TasksProcessor, TaskResult
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands
from batchmp.ffmptools.ffutils import (
    timed,
    run_cmd,
    CmdProcessingError,
    FFH
)

class SegmenterTask(Task):
    ''' Segment TasksProcessor task
    '''
    def __init__(self, fpath, backup_path,
                            ff_global_options, ff_other_options, preserve_metadata,
                            reset_timestamps, segment_size_MB, segment_length_secs):

        super().__init__(fpath, backup_path, ff_global_options, ff_other_options, preserve_metadata)

        # if needed, calculate segment duration via given file size
        if not segment_length_secs and segment_size_MB:
            split_factor = Segmenter._media_size_MB(self.fpath) / segment_size_MB
            split_factor  = split_factor if split_factor > 1.11 else 1.11
            segment_length_secs = Segmenter._media_duration(self.fpath) / split_factor

        self.cmd = ''.join((self.cmd,
                            FFmpegCommands.SEGMENT,
                            ' {0} {1}'.format(FFmpegCommands.SEGMENT_TIME, segment_length_secs),
                            FFmpegCommands.SEGMENT_RESET_TIMESTAMPS if reset_timestamps else ''))

    def execute(self):
        ''' builds and runs Segment FFmpeg command in a subprocess
        '''
        # store tags if needed
        self._store_tags()

        task_result = TaskResult()

        with temp_dir() as tmp_dir:
            # compile intermediary output path
            fn_parts = os.path.splitext(os.path.basename(self.fpath))
            fname_ext = fn_parts[1].strip().lower()
            fpath_output = ''.join((fn_parts[0], '_%d', fname_ext))
            fpath_output = os.path.join(tmp_dir, fpath_output)

            # build ffmpeg cmd string
            p_in = ''.join((self.cmd,
                            ' "{}"'.format(fpath_output)))

            # run ffmpeg command as a subprocess
            try:
                _, task_elapsed = run_cmd(p_in)
                task_result.add_task_step_duration(task_elapsed)
            except CmdProcessingError as e:
                task_result.add_task_step_info_msg('A problem while processing media file:\n\t{0}' \
                                                                    '\nOriginal error message:\n\t{1}' \
                                                                            .format(self.fpath, e.args[0]))
            else:
                # backup the original file if applicable
                if self.backup_path:
                    shutil.move(self.fpath, self.backup_path)

                # move split files to destination
                checker = UniqueDirNamesChecker(os.path.dirname(self.fpath))
                for fname in os.listdir(tmp_dir):
                    if fnmatch.fnmatch(fname, '*{}'.format(fname_ext)):
                        src_fpath = os.path.join(tmp_dir, fname)

                        # restore tags if needed
                        self._restore_tags(src_fpath)

                        dst_fname = checker.unique_name(fname)
                        dst_fpath = os.path.join(os.path.dirname(self.fpath), dst_fname)
                        shutil.move(src_fpath, dst_fpath)

        task_result.add_report_msg(self.fpath)
        return task_result


class Segmenter(FFMPRunner):
    @staticmethod
    def _media_duration(fpath):
        handler = MutagenTagHandler() + FFmpegTagHandler()
        if handler.can_handle(fpath):
            return handler.tag_holder.length
        else:
            return 0.0

    @staticmethod
    def _media_size_MB(fpath):
        return os.path.getsize(fpath) / 1024**2

    def segment(self, src_dir,
                    end_level = sys.maxsize, include = '*', exclude = '', sort = 'n',
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    segment_size_MB = 0.0, segment_length_secs = 0.0, backup = True,
                    ff_global_options = None, ff_other_options = None,
                    reset_timestamps = False, preserve_metadata = False):
        ''' Segment media file by specified size | duration
        '''
        cpu_core_time, total_elapsed = self.run(src_dir,
                                        end_level = end_level, sort = sort,
                                        include = include, exclude = exclude, quiet = quiet,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        segment_size_MB = segment_size_MB,
                                        segment_length_secs = segment_length_secs,
                                        serial_exec = serial_exec, backup=backup,
                                        ff_global_options = ff_global_options,
                                        ff_other_options = ff_other_options,
                                        reset_timestamps = reset_timestamps,
                                        preserve_metadata = preserve_metadata)
        # print run report
        if not quiet:
            self.run_report(cpu_core_time, total_elapsed)

    @timed
    def run(self, src_dir,
                end_level = sys.maxsize, include = '*', exclude = '', sort = 'n',
                filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                segment_size_MB = 0.0, segment_length_secs = 0.0, backup = True,
                ff_global_options = None, ff_other_options = None,
                reset_timestamps = False, preserve_metadata = False):

        ''' Perform segmentation by size | duration
        '''
        cpu_core_time = 0.0

        # validate input values
        if not segment_size_MB and not segment_length_secs:
            return cpu_core_time

        if segment_length_secs:
            # here need to determine media length
            pass_filter = lambda fpath: self._media_duration(fpath) > segment_length_secs
        elif segment_size_MB:
            # simple media selection by size
            pass_filter = lambda fpath: FFH.supported_media(fpath) and (self._media_size_MB(fpath) > segment_size_MB)


        media_files, backup_dirs = self._prepare_files(src_dir,
                                        end_level = end_level, sort = sort,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        pass_filter = pass_filter)

        if len(media_files) > 0:
            print('{0} media files to process'.format(len(media_files)))

            # build tasks
            tasks_params = ((media_file, backup_dir,
                                ff_global_options, ff_other_options, preserve_metadata,
                                reset_timestamps, segment_size_MB, segment_length_secs)
                                    for media_file, backup_dir in zip(media_files, backup_dirs))
            tasks = []
            for task_param in tasks_params:
                task = SegmenterTask(*task_param)
                tasks.append(task)

            cpu_core_time = TasksProcessor().process_tasks(tasks, serial_exec = serial_exec, quiet = quiet)
        else:
            print('No media files to process')

        return cpu_core_time



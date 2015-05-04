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


""" Batch splitting of media files
"""
import shutil, sys, os, math, fnmatch, shlex
from batchmp.commons.utils import temp_dir
from batchmp.ffmptools.ffrunner import FFMPRunner, FFMPRunnerTask, LogLevel
from batchmp.commons.taskprocessor import TaskResult
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands, FFmpegBitMaskOptions
from batchmp.ffmptools.ffutils import FFH
from batchmp.commons.utils import (
    timed,
    run_cmd,
    CmdProcessingError,
    MiscHelpers
)

class SegmenterTask(FFMPRunnerTask):
    ''' Segment TasksProcessor task
    '''
    def __init__(self, fpath, target_dir, log_level,
                            ff_general_options, ff_other_options, preserve_metadata,
                            reset_timestamps, segment_size_MB, segment_length_secs):

        super().__init__(fpath, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata)

        # calculate number of segments and, if needed, the segment length in secs
        if segment_length_secs:
            self.segment_length_secs = segment_length_secs
            self.num_segments = math.ceil(Segmenter._media_duration(self.fpath) / segment_length_secs)
        elif segment_size_MB:
            num_segments = Segmenter._media_size_MB(self.fpath) / segment_size_MB
            self.segment_length_secs = Segmenter._media_duration(self.fpath) / num_segments
            self.num_segments = math.ceil(num_segments)
        else:
            # should not really get there, but just in case
            raise ValueError('One of the command parameters needs to be specified: '\
                                                    '<segment_size_MB | segment_length_secs>')
        self.reset_timestamps = reset_timestamps

    @property
    def ff_cmd(self):
        ''' Fragment command builder
        '''
        return ''.join((super().ff_cmd,
                            FFmpegCommands.SEGMENT,
                            ' {0} {1}'.format(FFmpegCommands.SEGMENT_TIME, self.segment_length_secs),
                            FFmpegCommands.SEGMENT_RESET_TIMESTAMPS if self.reset_timestamps else ''))

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
            fpath_output = ''.join((fn_parts[0],
                                   '_%{}d'.format(MiscHelpers.int_num_digits(self.num_segments)),
                                   fname_ext))
            fpath_output = os.path.join(tmp_dir, fpath_output)

            # build ffmpeg cmd string
            p_in = ''.join((self.ff_cmd, ' {}'.format(shlex.quote(fpath_output))))
            self._log(p_in, LogLevel.FFMPEG)

            # run ffmpeg command as a subprocess
            try:
                _, task_elapsed = run_cmd(p_in)
                task_result.add_task_step_duration(task_elapsed)
            except CmdProcessingError as e:
                task_result.add_task_step_info_msg('A problem while processing media file:\n\t{0}' \
                                                                    '\nOriginal error message:\n\t{1}' \
                                                                            .format(self.fpath, e.args[0]))
            else:
                # move split files to target directory
                for segmented_fname in os.listdir(tmp_dir):
                    if fnmatch.fnmatch(segmented_fname, '*{}'.format(fname_ext)):
                        segmented_fpath = os.path.join(tmp_dir, segmented_fname)

                        # restore tags if needed
                        self._restore_tags(segmented_fpath)

                        # move fragmented file to target dir
                        shutil.move(segmented_fpath, self.target_dir)

                # all well
                task_result.succeeded = True

        task_result.add_report_msg(self.fpath)
        return task_result


class Segmenter(FFMPRunner):
    def segment(self, src_dir,
                    end_level = sys.maxsize, include = None, exclude = None,
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    segment_size_MB = 0.0, segment_length_secs = 0.0,
                    target_dir = None, log_level = None,
                    ff_general_options = None, ff_other_options = None,
                    reset_timestamps = False, preserve_metadata = False):

        ''' Segment media file by specified size | duration
        '''
        tasks = []
        if segment_size_MB or segment_length_secs:
            if segment_length_secs:
                # here need to determine media length
                pass_filter = lambda fpath: self._media_duration(fpath) > segment_length_secs
            elif segment_size_MB:
                # simple media selection by size
                pass_filter = lambda fpath: FFH.supported_media(fpath) and (self._media_size_MB(fpath) > segment_size_MB)

            media_files, target_dirs = self._prepare_files(src_dir,
                                            end_level = end_level,
                                            include = include, exclude = exclude,
                                            filter_dirs = filter_dirs, filter_files = filter_files,
                                            target_dir = target_dir, target_dir_prefix = 'segmented',
                                            pass_filter = pass_filter)
            # build tasks
            tasks_params = [(media_file, target_dir_path, log_level,
                                ff_general_options, ff_other_options, preserve_metadata,
                                reset_timestamps, segment_size_MB, segment_length_secs)
                                    for media_file, target_dir_path in zip(media_files, target_dirs)]
            for task_param in tasks_params:
                task = SegmenterTask(*task_param)
                tasks.append(task)

        # run tasks
        self.run_tasks(tasks, serial_exec = serial_exec, quiet = quiet)


    # Internal Helpers
    @staticmethod
    def _media_duration(fpath):
        handler = MutagenTagHandler() + FFmpegTagHandler()
        if handler.can_handle(fpath):
            return handler.tag_holder.length
        else:
            return 0.0

    @staticmethod
    def _media_size_MB(fpath):
        return os.path.getsize(fpath) / 1000**2

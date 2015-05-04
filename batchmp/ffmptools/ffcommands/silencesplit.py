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


""" Batch split on silence
"""
import shutil, sys, os, fnmatch, shlex
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

class SilenceSplitterTask(FFMPRunnerTask):
    ''' Segment TasksProcessor task
    '''
    DEFAULT_SILENCE_START_PADDING_IN_SECS = 2

    def __init__(self, fpath, target_dir, log_level,
                            ff_general_options, ff_other_options, preserve_metadata,
                            reset_timestamps, silence_min_duration, silence_noise_tolerance_amplitude_ratio):

        super().__init__(fpath, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata)

        self.reset_timestamps = reset_timestamps
        self.silence_min_duration = silence_min_duration
        self.silence_noise_tolerance_amplitude_ratio = silence_noise_tolerance_amplitude_ratio

    def ff_cmd(self, segment_start_times):
        ''' Silence Splitter command builder
        '''
        return ''.join((super().ff_cmd,
                            FFmpegCommands.SEGMENT,
                            ' {0} {1}'.format(FFmpegCommands.SEGMENT_TIMES, ','.join(segment_start_times)),
                            FFmpegCommands.SEGMENT_RESET_TIMESTAMPS if self.reset_timestamps else ''))

    def execute(self):
        ''' builds and runs Segment FFmpeg command in a subprocess
        '''

        task_result = TaskResult()

        segment_start_times, task_elapsed = self._segment_start_times()
        task_result.add_task_step_duration(task_elapsed)
        if not segment_start_times:
            task_result.add_task_step_info_msg( \
                                        'No silence detected in media file:\n\t{0}'.format(self.fpath))
        else:
            # store tags if needed
            self._store_tags()

            with temp_dir() as tmp_dir:
                # compile intermediary output path
                fn_parts = os.path.splitext(os.path.basename(self.fpath))
                fname_ext = fn_parts[1].strip().lower()
                fpath_output = ''.join((fn_parts[0],
                                       '_%{}d'.format(MiscHelpers.int_num_digits(len(segment_start_times))),
                                       fname_ext))
                fpath_output = os.path.join(tmp_dir, fpath_output)

                # build ffmpeg cmd string
                p_in = ''.join((self.ff_cmd(segment_start_times), ' {}'.format(shlex.quote(fpath_output))))
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

    @timed
    def _segment_start_times(self):
        silence_entries = FFH.silence_detector(self.fpath,
                         min_duration = self.silence_min_duration,
                         noise_tolerance_amplitude_ratio = self.silence_noise_tolerance_amplitude_ratio)
        segment_start_times = []
        for silence_entry in silence_entries:
            silence_padding = (silence_entry.silence_end - silence_entry.silence_start) / 2
            if silence_padding > self.DEFAULT_SILENCE_START_PADDING_IN_SECS:
                silence_padding = self.DEFAULT_SILENCE_START_PADDING_IN_SECS

            segment_start_times.append(str(silence_entry.silence_start + silence_padding))

        return segment_start_times


class SilenceSplitter(FFMPRunner):
    DEFAULT_SILENCE_MIN_DURATION_IN_SECS = 2
    DEFAULT_SILENCE_NOISE_TOLERANCE = 0.002

    def silence_split(self, src_dir,
                    end_level = sys.maxsize, include = None, exclude = None,
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    target_dir = None, log_level = None,
                    ff_general_options = None, ff_other_options = None,
                    reset_timestamps = False, preserve_metadata = False,
                    silence_min_duration = None, silence_noise_tolerance_amplitude_ratio = None):

        ''' Segment media file by specified silence
        '''
        if not silence_min_duration:
            silence_min_duration = self.DEFAULT_SILENCE_MIN_DURATION_IN_SECS
        if not silence_noise_tolerance_amplitude_ratio:
            silence_noise_tolerance_amplitude_ratio = self.DEFAULT_SILENCE_NOISE_TOLERANCE

        media_files, target_dirs = self._prepare_files(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        target_dir = target_dir, target_dir_prefix = 'silence_split')
        # build tasks
        tasks = []
        tasks_params = [(media_file, target_dir_path, log_level,
                            ff_general_options, ff_other_options, preserve_metadata,
                            reset_timestamps, silence_min_duration, silence_noise_tolerance_amplitude_ratio)
                                for media_file, target_dir_path in zip(media_files, target_dirs)]
        for task_param in tasks_params:
            task = SilenceSplitterTask(*task_param)
            tasks.append(task)

        # run tasks
        self.run_tasks(tasks, serial_exec = serial_exec, quiet = quiet)

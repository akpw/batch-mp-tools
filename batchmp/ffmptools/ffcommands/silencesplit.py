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
    def __init__(self, fpath, target_dir, log_level,
                            ff_general_options, ff_other_options, preserve_metadata,
                            reset_timestamps, silence_min_duration, silence_noise_tolerance_amplitude_ratio, 
                            silence_auto_duration, silence_target_trimmed_duration):

        super().__init__(fpath, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata)

        self.reset_timestamps = reset_timestamps
        self.silence_min_duration = silence_min_duration
        self.silence_noise_tolerance_amplitude_ratio = silence_noise_tolerance_amplitude_ratio
        self.silence_auto_duration = silence_auto_duration
        self.silence_target_trimmed_duration = silence_target_trimmed_duration

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
        
        # silence entry duration
        duration = lambda silence_entry: silence_entry.silence_end - silence_entry.silence_start
        
        # auto-duration filter
        if self.silence_auto_duration:            
            durations = [duration(silence_entry) for silence_entry in silence_entries]
            min_duration = MiscHelpers.percentile(durations, 25)        
            silence_entries = [silence_entry for silence_entry in silence_entries if duration(silence_entry) > min_duration]

        segment_start_times = []
        for silence_entry in silence_entries:
            # trim silences start duration
            silence_start = lambda silence_entry : silence_entry.silence_start \
                    if duration(silence_entry) < self.silence_target_trimmed_duration \
                                              else silence_entry.silence_end - self.silence_target_trimmed_duration
            segment_start_times.append(str(silence_start(silence_entry)))

        return segment_start_times


class SilenceSplitter(FFMPRunner):
    def silence_split(self, ff_entry_params):
        ''' Segment media file by specified silence
        '''

        ff_entry_params.target_dir_prefix = 'silence_split'
        media_files, target_dirs = self._prepare_files(ff_entry_params)

        # build tasks
        tasks = []        
        tasks_params = [(media_file, target_dir_path, ff_entry_params.log_level, ff_entry_params.ff_general_options, 
                            ff_entry_params.ff_other_options, ff_entry_params.preserve_metadata, ff_entry_params.reset_timestamps, 
                            ff_entry_params.silence_min_duration, ff_entry_params.silence_noise_tolerance_amplitude_ratio, 
                            ff_entry_params.silence_auto_duration, ff_entry_params.silence_target_trimmed_duration)
                                for media_file, target_dir_path in zip(media_files, target_dirs)]

        for task_param in tasks_params:
            task = SilenceSplitterTask(*task_param)
            tasks.append(task)

        # run tasks
        self.run_tasks(tasks, serial_exec = ff_entry_params.serial_exec, quiet = ff_entry_params.quiet)


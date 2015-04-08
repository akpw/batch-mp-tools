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
import shutil, sys, os, fnmatch
from batchmp.commons.utils import temp_dir
from batchmp.ffmptools.ffrunner import FFMPRunner, FFMPRunnerTask
from batchmp.commons.taskprocessor import TasksProcessor, TaskResult
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands
from batchmp.ffmptools.ffutils import FFH
from batchmp.commons.utils import (
    timed,
    run_cmd,
    CmdProcessingError
)

class SilenceSplitterTask(FFMPRunnerTask):
    ''' Segment TasksProcessor task
    '''
    def __init__(self, fpath, target_dir,
                            ff_global_options, ff_other_options, preserve_metadata,
                            reset_timestamps, silence_min_duration, silence_noise_tolerance_amplitude_ratio):

        super().__init__(fpath, target_dir, ff_global_options, ff_other_options, preserve_metadata)


        self.cmd = ''.join((self.cmd,
                            FFmpegCommands.SEGMENT,
                            ' {0} {1}'.format(FFmpegCommands.SEGMENT_TIME, segment_length_secs),
                            FFmpegCommands.SEGMENT_RESET_TIMESTAMPS if reset_timestamps else ''))

        # try to explicitly tell FFMpeg to preserve the original quality
        self._FF_preserve_quality()

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
                # move split files to target directory
                for segmented_fname in os.listdir(tmp_dir):
                    if fnmatch.fnmatch(segmented_fname, '*{}'.format(fname_ext)):
                        segmented_fpath = os.path.join(tmp_dir, segmented_fname)

                        # restore tags if needed
                        self._restore_tags(segmented_fpath)

                        # move fragmented file to target dir
                        shutil.move(segmented_fpath, self.target_dir)

        task_result.add_report_msg(self.fpath)
        return task_result


    def _segment_times():
        pass




class SilenceSplitter(FFMPRunner):
    def silence_split(self, src_dir,
                    end_level = sys.maxsize, include = None, exclude = None,
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    target_dir = None,
                    ff_global_options = None, ff_other_options = None,
                    reset_timestamps = False, preserve_metadata = False,
                    silence_min_duration = None, silence_noise_tolerance_amplitude_ratio = None):
        ''' Segment media file by specified size | duration
        '''
        cpu_core_time, total_elapsed = self.run(src_dir,
                            end_level = end_level,
                            include = include, exclude = exclude, quiet = quiet,
                            filter_dirs = filter_dirs, filter_files = filter_files,
                            silence_min_duration = silence_min_duration,
                            silence_noise_tolerance_amplitude_ratio = silence_noise_tolerance_amplitude_ratio,
                            serial_exec = serial_exec, target_dir = target_dir,
                            ff_global_options = ff_global_options,
                            ff_other_options = ff_other_options,
                            reset_timestamps = reset_timestamps,
                            preserve_metadata = preserve_metadata)
        # print run report
        if not quiet:
            self.run_report(cpu_core_time, total_elapsed)

    @timed
    def run(self, src_dir,
                    end_level = sys.maxsize, include = None, exclude = None,
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    target_dir = None,
                    ff_global_options = None, ff_other_options = None,
                    reset_timestamps = False, preserve_metadata = False,
                    silence_min_duration = None, silence_noise_tolerance_amplitude_ratio = None):

        ''' Perform segmentation by size | duration
        '''
        cpu_core_time = 0.0

        media_files, target_dirs = self._prepare_files(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        target_dir = target_dir, target_dir_prefix = 'silence_split')

        if len(media_files) > 0:
            print('{0} media files to process'.format(len(media_files)))

            # build tasks
            tasks_params = ((media_file, target_dir_path,
                                ff_global_options, ff_other_options, preserve_metadata,
                                reset_timestamps, silence_min_duration, silence_noise_tolerance_amplitude_ratio)
                                    for media_file, target_dir_path in zip(media_files, target_dirs))
            tasks = []
            for task_param in tasks_params:
                task = SilenceSplitterTask(*task_param)
                tasks.append(task)

            cpu_core_time = TasksProcessor().process_tasks(tasks, serial_exec = serial_exec, quiet = quiet)
        else:
            print('No media files to process')

        return cpu_core_time












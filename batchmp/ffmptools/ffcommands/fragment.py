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


""" Batch Fragmentation of media files
"""
import shutil, sys, os
from batchmp.commons.utils import temp_dir
from batchmp.ffmptools.ffrunner import FFMPRunner, FFMPRunnerTask, LogLevel
from batchmp.commons.taskprocessor import TasksProcessor, TaskResult
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands, FFmpegBitMaskOptions
from batchmp.commons.utils import (
    timed,
    run_cmd,
    CmdProcessingError
)

class FragmenterTask(FFMPRunnerTask):
    ''' Fragment TasksProcessor task
    '''
    def __init__(self, fpath, target_dir, log_level,
                            ff_general_options, ff_other_options, preserve_metadata,
                            fragment_starttime, fragment_duration):

        super().__init__(fpath, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata)

        if not self.ff_general_options:
            self.ff_general_options = FFmpegBitMaskOptions.ff_general_options(
                                  FFmpegBitMaskOptions.COPY_CODECS | FFmpegBitMaskOptions.MAP_ALL_STREAMS)

            if not self.ff_other_options:
                self.ff_other_options = self._ff_cmd_exclude_artwork_streams()

        self.fragment_starttime = fragment_starttime
        self.fragment_duration = fragment_duration

    @property
    def ff_cmd(self):
        ''' Fragment command builder
        '''
        return ''.join((super().ff_cmd,
                            ' -ss {}'.format(self.fragment_starttime),
                            ' -t {}'.format(self.fragment_duration)
                            ))

    def execute(self):
        ''' builds and runs Fragment FFmpeg command in a subprocess
        '''
        # store tags if needed
        self._store_tags()

        task_result = TaskResult()

        with temp_dir() as tmp_dir:
            # prepare the tmp output path
            fragmented_fpath = os.path.join(tmp_dir, os.path.basename(self.fpath))

            # build ffmpeg cmd string
            p_in = '{0} "{1}"'.format(self.ff_cmd, fragmented_fpath)
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
                # restore tags if needed
                self._restore_tags(fragmented_fpath)

                # move fragmented file to target dir
                shutil.move(fragmented_fpath, self.target_dir)

        task_result.add_report_msg(self.fpath)
        return task_result


class Fragmenter(FFMPRunner):
    def fragment(self, src_dir,
                    end_level = sys.maxsize, include = None, exclude = None,
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    fragment_starttime = None, fragment_duration = None,
                    target_dir = None, log_level = None,
                    ff_general_options = None, ff_other_options = None,
                    preserve_metadata = False):
        ''' Fragment media file by specified starttime & duration
        '''
        cpu_core_time, total_elapsed = self.run(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude, quiet = quiet,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        fragment_starttime = fragment_starttime,
                                        fragment_duration = fragment_duration,
                                        serial_exec = serial_exec,
                                        target_dir = target_dir, log_level = log_level,
                                        ff_general_options = ff_general_options,
                                        ff_other_options = ff_other_options,
                                        preserve_metadata = preserve_metadata)
        # print run report
        if not quiet:
            self.run_report(cpu_core_time, total_elapsed)

    @timed
    def run(self, src_dir,
                end_level = sys.maxsize, include = None, exclude = None,
                filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                fragment_starttime = None, fragment_duration = None,
                target_dir = None, log_level = None,
                ff_general_options = None, ff_other_options = None,
                preserve_metadata = False):

        cpu_core_time = 0.0

        # validate input values
        if (fragment_starttime is None) or (fragment_duration is None):
            return cpu_core_time

        media_files, target_dirs = self._prepare_files(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        target_dir = target_dir, target_dir_prefix = 'fragmented')
        if len(media_files) > 0:
            print('{0} media files to process'.format(len(media_files)))

            # build tasks
            tasks_params = ((media_file, target_dir_path, log_level,
                                ff_general_options, ff_other_options, preserve_metadata,
                                fragment_starttime, fragment_duration)
                                    for media_file, target_dir_path in zip(media_files, target_dirs))
            tasks = []
            for task_param in tasks_params:
                task = FragmenterTask(*task_param)
                tasks.append(task)

            cpu_core_time = TasksProcessor().process_tasks(tasks, serial_exec = serial_exec, quiet = quiet)
        else:
            print('No media files to process')

        return cpu_core_time


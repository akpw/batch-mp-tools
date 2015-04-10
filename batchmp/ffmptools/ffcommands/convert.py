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


""" Batch Conversion of media files
"""
import shutil, sys, os
from batchmp.commons.utils import temp_dir
from batchmp.ffmptools.ffrunner import FFMPRunner, FFMPRunnerTask, LogLevel
from batchmp.commons.taskprocessor import TasksProcessor, TaskResult
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands
from batchmp.commons.utils import (
    timed,
    run_cmd,
    CmdProcessingError
)

class ConvertorTask(FFMPRunnerTask):
    ''' Conversion TasksProcessor task
    '''
    def __init__(self, fpath, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata,
                                                            target_format, convert_options):

        super().__init__(fpath, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata)

        # check convert options
        convert_options = convert_options or FFmpegCommands.CONVERT_COPY_VBR_QUALITY # default
        if convert_options == FFmpegCommands.CONVERT_LOSSLESS:
            # see if lossless is appropriate
            # TBD: video formats
            if target_format == '.flac':
                convert_options = FFmpegCommands.CONVERT_LOSSLESS_FLAC
            elif target_format == '.m4a':
                convert_options = FFmpegCommands.CONVERT_LOSSLESS_ALAC
            else:
                convert_options = FFmpegCommands.CONVERT_COPY_VBR_QUALITY

        self.target_format = target_format
        self.convert_options = convert_options

    @property
    def ff_cmd(self):
        ''' Convert command builder
        '''
        return ''.join((super().ff_cmd, self.convert_options))

    def execute(self):
        ''' builds and runs FFmpeg Conversion command in a subprocess
        '''
        # store tags if needed
        self._store_tags()

        task_result = TaskResult()

        with temp_dir() as tmp_dir:
            # prepare the tmp output path
            conv_fname = ''.join((os.path.splitext(os.path.basename(self.fpath))[0], self.target_format))
            conv_fpath = os.path.join(tmp_dir, conv_fname)

            # build ffmpeg cmd string
            p_in = ''.join((self.ff_cmd, ' "{}"'.format(conv_fpath)))
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
                self._restore_tags(conv_fpath)

                # move converted file to target dir
                shutil.move(conv_fpath, self.target_dir)

        task_result.add_report_msg(self.fpath)

        return task_result


class Convertor(FFMPRunner):
    def convert(self, src_dir,
                    end_level = sys.maxsize, include = None, exclude = None,
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    target_format = None, convert_options = None,
                    target_dir = None, log_level = None,
                    ff_general_options = None, ff_other_options = None,
                    preserve_metadata = False):
        ''' Converts media to specified format
        '''
        cpu_core_time, total_elapsed = self.run(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude, quiet = quiet,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        target_format = target_format, convert_options = convert_options,
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
                target_format = None, convert_options = None, target_dir = None,
                ff_general_options = None, ff_other_options = None,
                preserve_metadata = False, log_level = None):

        cpu_core_time = 0.0

        # validate input values
        if not target_format:
            return cpu_core_time

        if target_format.startswith('.'):
            target_dir_prefix = '{}'.format(target_format[1:])
        else:
            target_dir_prefix = '{}'.format(target_format)
            target_format = '.{}'.format(target_format)

        media_files, target_dirs = self._prepare_files(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        target_dir = target_dir, target_dir_prefix = target_dir_prefix)
        if len(media_files) > 0:
            print('{0} media files to process'.format(len(media_files)))

            # build tasks
            tasks_params = ((media_file, target_dir_path, log_level,
                                ff_general_options, ff_other_options, preserve_metadata,
                                target_format, convert_options)
                                    for media_file, target_dir_path in zip(media_files, target_dirs))
            tasks = []
            for task_param in tasks_params:
                task = ConvertorTask(*task_param)
                tasks.append(task)

            cpu_core_time = TasksProcessor().process_tasks(tasks, serial_exec = serial_exec, quiet = quiet)
        else:
            print('No media files to process')

        return cpu_core_time



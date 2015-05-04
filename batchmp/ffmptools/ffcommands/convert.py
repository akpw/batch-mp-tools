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
import shutil, sys, os, shlex
from batchmp.commons.utils import temp_dir
from batchmp.ffmptools.ffrunner import FFMPRunner, FFMPRunnerTask, LogLevel
from batchmp.commons.taskprocessor import TaskResult
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands, FFmpegBitMaskOptions
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
                                                            target_format):
        self.target_format = target_format

        super().__init__(fpath, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata)

    def _check_defaults(self):
        if not self.ff_other_options:
            self.ff_other_options = FFmpegCommands.CONVERT_COPY_VBR_QUALITY
        elif self.ff_other_options == FFmpegCommands.CONVERT_LOSSLESS:
            # see if lossless is appropriate
            # TBD: video formats
            if self.target_format == '.flac':
                self.ff_other_options = FFmpegCommands.CONVERT_LOSSLESS_FLAC
            elif self.target_format == '.m4a':
                self.ff_other_options = FFmpegCommands.CONVERT_LOSSLESS_ALAC
            else:
                self.ff_other_options = FFmpegCommands.CONVERT_COPY_VBR_QUALITY

        if not self.ff_general_options:
            self.ff_general_options = FFmpegBitMaskOptions.ff_general_options(
                                                    FFmpegBitMaskOptions.MAP_ALL_STREAMS)

            if self.ff_other_options in (FFmpegCommands.CONVERT_COPY_VBR_QUALITY,
                                         FFmpegCommands.CONVERT_LOSSLESS_FLAC,
                                         FFmpegCommands.CONVERT_LOSSLESS_ALAC,
                                         FFmpegCommands.CONVERT_CHANGE_CONTAINER):
                self.ff_other_options += self._ff_cmd_exclude_artwork_streams()

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
            p_in = ''.join((self.ff_cmd, ' {}'.format(shlex.quote(conv_fpath))))
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

                # all well
                task_result.succeeded = True

        task_result.add_report_msg(self.fpath)
        return task_result


class Convertor(FFMPRunner):
    def convert(self, src_dir,
                    end_level = sys.maxsize, include = None, exclude = None,
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    target_format = None,
                    target_dir = None, log_level = None,
                    ff_general_options = None, ff_other_options = None,
                    preserve_metadata = False):

        ''' Converts media to specified format
        '''
        tasks = []
        if target_format:
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
            # build tasks
            tasks_params = [(media_file, target_dir_path, log_level,
                                ff_general_options, ff_other_options, preserve_metadata,
                                target_format)
                                    for media_file, target_dir_path in zip(media_files, target_dirs)]
            for task_param in tasks_params:
                task = ConvertorTask(*task_param)
                tasks.append(task)

        # run tasks
        self.run_tasks(tasks, serial_exec = serial_exec, quiet = quiet)





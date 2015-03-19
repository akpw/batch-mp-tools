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
from batchmp.fstools.fsutils import temp_dir, UniqueDirNamesChecker
from batchmp.ffmptools.ffrunner import FFMPRunner
from batchmp.ffmptools.taskpp import Task, TasksProcessor, TaskResult
from batchmp.ffmptools.ffutils import (
    timed,
    run_cmd,
    CmdProcessingError,
    FFH
)

class ConvertorTask(Task):
    ''' Conversion TasksProcessor task
    '''
    def __init__(self, fpath, backup_path,
                                ff_global_options, ff_other_options, preserve_metadata,
                                                        target_format, convert_options):

        super().__init__(fpath, backup_path, ff_global_options, ff_other_options, preserve_metadata)

        self.target_format = target_format
        self.cmd = ''.join((self.cmd,
                            ' {}'.format(convert_options) if convert_options else ''))

    def execute(self):
        ''' builds and runs FFmpeg Conversion command in a subprocess
        '''
        # store tags if needed
        self._store_tags()

        task_result = TaskResult()

        with temp_dir() as tmp_dir:
            # prepare the tmp output path
            cv_name = ''.join((os.path.splitext(os.path.basename(self.fpath))[0], self.target_format))
            cv_path = os.path.join(tmp_dir, cv_name)

            # build ffmpeg cmd string
            p_in = ''.join((self.cmd,
                            ' "{}"'.format(cv_path)))

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
                self._restore_tags(cv_path)

                # backup the original file if applicable
                if self.backup_path:
                    shutil.move(self.fpath, self.backup_path)

                # move media fragment to destination
                checker = UniqueDirNamesChecker(os.path.dirname(self.fpath))
                dst_fname = checker.unique_name(cv_name)
                dst_fpath = os.path.join(os.path.dirname(self.fpath), dst_fname)
                shutil.move(cv_path, dst_fpath)

        task_result.add_report_msg(self.fpath)

        return task_result


class Convertor(FFMPRunner):
    def convert(self, src_dir,
                    end_level = sys.maxsize, include = '*', exclude = '', sort = 'n',
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    target_format = None, convert_options = None, backup = True,
                    ff_global_options = None, ff_other_options = None,
                    preserve_metadata = False):
        ''' Converts media to specified format
        '''
        cpu_core_time, total_elapsed = self.run(src_dir,
                                        end_level = end_level, sort = sort,
                                        include = include, exclude = exclude, quiet = quiet,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        target_format = target_format, convert_options = convert_options,
                                        serial_exec = serial_exec, backup = backup,
                                        ff_global_options = ff_global_options,
                                        ff_other_options = ff_other_options,
                                        preserve_metadata = preserve_metadata)
        # print run report
        if not quiet:
            self.run_report(cpu_core_time, total_elapsed)

    @timed
    def run(self, src_dir,
                end_level = sys.maxsize, include = '*', exclude = '', sort = 'n',
                filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                target_format = None, convert_options = None, backup = True,
                ff_global_options = None, ff_other_options = None,
                preserve_metadata = False):

        cpu_core_time = 0.0

        # validate input values
        if not target_format:
            return cpu_core_time
        if not target_format.startswith('.'):
            target_format = '.{}'.format(target_format)

        media_files, backup_dirs = self._prepare_files(src_dir,
                                        end_level = end_level, sort = sort,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files)
        if len(media_files) > 0:
            print('{0} media files to process'.format(len(media_files)))

            # build tasks
            tasks_params = ((media_file, backup_dir,
                                ff_global_options, ff_other_options, preserve_metadata,
                                target_format, convert_options)
                                    for media_file, backup_dir in zip(media_files, backup_dirs))
            tasks = []
            for task_param in tasks_params:
                task = ConvertorTask(*task_param)
                tasks.append(task)

            cpu_core_time = TasksProcessor().process_tasks(tasks, serial_exec = serial_exec, quiet = quiet)
        else:
            print('No media files to process')

        return cpu_core_time



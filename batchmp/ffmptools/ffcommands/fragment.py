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

import shutil, sys, os, datetime, math, fnmatch
from batchmp.fstools.fsutils import temp_dir, UniqueDirNamesChecker
from batchmp.ffmptools.ffrunner import FFMPRunner
from batchmp.ffmptools.taskpp import Task, TasksProcessor, TaskResult
from batchmp.ffmptools.ffutils import (
    timed,
    run_cmd,
    CmdProcessingError,
    FFH
)

class FragmenterTask(Task):
    ''' A specific TasksProcessor task
    '''
    def __init__(self, fpath, backup_path, fragment_starttime, fragment_duration, replace_original):
        ''' inits the task parameters
        '''
        self.fpath = fpath
        self.backup_path = backup_path
        self.fragment_starttime = fragment_starttime
        self.fragment_duration = fragment_duration
        self.replace_original = replace_original

    def execute(self):
        ''' builds and runs FFmpeg command in a subprocess
        '''
        task_result = TaskResult()
        with temp_dir() as tmp_dir:
            checker = UniqueDirNamesChecker(os.path.dirname(self.fpath))

            # prepare the tmp output path
            fn_parts = os.path.splitext(os.path.basename(self.fpath))
            fname_ext = fn_parts[1].strip().lower()

            fr_name = ''.join((fn_parts[0], '_fr', fname_ext))
            fr_path = os.path.join(tmp_dir, fr_name)

            # build ffmpeg cmd string
            p_in = ''.join(('ffmpeg',
                            ' -v error',
                            ' -i "{}"'.format(self.fpath),
                            ' -c copy',
                            ' -ss {}'.format(self.fragment_starttime),
                            ' -t {}'.format(self.fragment_duration),
                            ' "{}"'.format(fr_path)))

            # run ffmpeg command as a subprocess
            try:
                _, task_elapsed = run_cmd(p_in)
                task_result.add_task_step_duration(task_elapsed)
            except CmdProcessingError as e:
                task_result.add_task_step_info_msg('A problem while processing media file:\n\t{0}'
                                                '\nOriginal error message:\n\t{1}'
                                                        .format(self.fpath, e.args[0]))
            else:
                # backup the original file if applicable
                if self.backup_path != None:
                    shutil.move(self.fpath, self.backup_path)

                # move media fragment to destination
                if not self.replace_original:
                    dst_fname = checker.unique_name(fr_name)
                    dst_fpath = os.path.join(os.path.dirname(self.fpath), dst_fname)
                    shutil.move(fr_path, dst_fpath)
                else:
                    shutil.move(fr_path, self.fpath)

        # log report
        td = datetime.timedelta(seconds = math.ceil(task_result.task_duration))
        task_result.add_task_step_info_msg('Done processing\n {0}\n in {1}'.format(self.fpath, str(td)))

        return task_result


class Fragmenter(FFMPRunner):
    def fragment(self, src_dir,
                    end_level = sys.maxsize, include = '*', exclude = '', sort = 'n',
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    fragment_starttime = None, fragment_duration = None,
                    backup = True, replace_original = False):
        ''' Fragment media file by specified starttime & duration
        '''
        cpu_core_time, total_elapsed = self.run(src_dir,
                                        end_level = end_level, sort = sort,
                                        include = include, exclude = exclude, quiet = quiet,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        fragment_starttime = fragment_starttime,
                                        fragment_duration = fragment_duration,
                                        backup = backup, replace_original = replace_original)
        # print run report
        if not quiet:
            self.run_report(cpu_core_time, total_elapsed)

    @timed
    def run(self, src_dir,
                end_level = sys.maxsize, include = '*', exclude = '', sort = 'n',
                filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                fragment_starttime = None, fragment_duration = None,
                backup = True, replace_original = False):

        ''' Perform segmentation by size | duration
        '''
        cpu_core_time = 0.0

        # validate input values
        if (not fragment_starttime) or (not fragment_duration):
            return cpu_core_time

        media_files = [f for f in FFH.media_files(src_dir,
                                        end_level = end_level, sort = sort,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files)]

        if len(media_files) > 0:
            # if backup is required, prepare the backup dirs
            if backup:
                backup_dirs = FFH.setup_backup_dirs(media_files)
            else:
                backup_dirs = [None for bd in media_files]

            print('{0} media files to process'.format(len(media_files)))

            # build tasks
            tasks_params = ((media_file, backup_dir, fragment_starttime, fragment_duration, replace_original)
                                    for media_file, backup_dir in zip(media_files, backup_dirs))
            tasks = []
            for task_param in tasks_params:
                task = FragmenterTask(*task_param)
                tasks.append(task)

            cpu_core_time = TasksProcessor().process_tasks(tasks, serial_exec = serial_exec)
        else:
            print('No media files to process')

        return cpu_core_time









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


""" Batch Reduce of background audio noise in media files,
    via filtering out highpass / low-pass frequencies

    Uses batchmp.ffmptools.taskpp.TasksProcessor to leverage available CPU cores

    Supports multi-passes processing, e.g. 3 times for each media file
    Supports backing up original media in their respective folders
"""

import shutil, sys, os, datetime, math
from batchmp.fstools.fsutils import temp_dir
from batchmp.ffmptools.ffrunner import FFMPRunner
from batchmp.ffmptools.taskpp import Task, TasksProcessor, TaskResult
from batchmp.ffmptools.ffutils import (
    timed,
    run_cmd,
    CmdProcessingError,
    FFH
)

class DenoiserTask(Task):
    ''' A specific TasksProcessor task
    '''
    def __init__(self, fpath, backup_path, highpass, lowpass, num_passes):
        ''' inits the task parameters
        '''
        self.fpath = fpath
        self.backup_path = backup_path
        self.highpass = highpass
        self.lowpass = lowpass
        self.num_passes = num_passes

    def execute(self):
        ''' builds and runs FFmpeg command in a subprocess
        '''
        fname = os.path.basename(self.fpath)
        fname_ext = os.path.splitext(fname)[1].strip().lower()

        # build ffmpeg -af parameter
        if self.highpass and self.lowpass:
            af_str = 'highpass=f={0}, lowpass=f={1}'.format(self.highpass, self.lowpass)
        elif self.lowpass:
            af_str = 'lowpass=f={}'.format(self.lowpass)
        elif self.highpass:
            af_str = 'highpass=f={}'.format(self.highpass)

        # ffmpeg initial input path
        fpath_input = self.fpath
        task_result = TaskResult()

        with temp_dir() as tmp_dir:
            # process the file in given number of passes
            for pass_cnt in range(self.num_passes):

                # compile intermediary output path
                fpath_output = ''.join((os.path.splitext(fname)[0],
                                        '_{}'.format(datetime.datetime.now().strftime("%H%M%S%f")),
                                        fname_ext))
                fpath_output = os.path.join(tmp_dir, fpath_output)

                p_in = ''.join(('ffmpeg',
                            ' -v error',
                            ' -i "{}"'.format(fpath_input),
                            ' -af "{}"'.format(af_str),
                            ' "{}"'.format(fpath_output)))

                # run ffmpeg command as a subprocess
                try:
                    _, pass_elapsed = run_cmd(p_in)
                except CmdProcessingError as e:
                    task_result.add_task_step_info_msg('A problem while processing media file:\n\t{0}'
                                  '\nSkipping further processing at pass {1} ...'
                                  '\nOriginal error message:\n\t{2}'
                                  .format(fpath_input, pass_cnt + 1, e.args[0]))
                    break
                else:
                    task_result.add_task_step_duration(pass_elapsed)

                if pass_cnt == self.num_passes - 1:
                    # for the last pass,
                    # backup the original file if applicable
                    if self.backup_path:
                        shutil.move(self.fpath, self.backup_path)
                    # ... and replace it with the resulting output
                    shutil.move(fpath_output, self.fpath)
                else:
                    # for the next pass, make the intermediary output new input
                    fpath_input = fpath_output

        # log report
        td = datetime.timedelta(seconds = math.ceil(task_result.task_duration))
        task_result.add_task_step_info_msg('Done processing:\n {0}\n {2} {3} in {1}'.format(
                                self.fpath, str(td),
                                self.num_passes, 'passes' if self.num_passes > 1 else 'pass'))
        return task_result

class Denoiser(FFMPRunner):
    def apply_af_filters(self, src_dir,
                            end_level = sys.maxsize, include = '*', exclude = '', sort = 'n',
                            filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                            num_passes = 1, highpass = None, lowpass = None, backup=True):

        cpu_core_time, total_elapsed = self.run(src_dir,
                                        end_level = end_level, sort = sort,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        quiet = quiet, num_passes = num_passes, serial_exec = serial_exec,
                                        highpass = highpass, lowpass = lowpass, backup=backup)
        # print run report
        if not quiet:
            self.run_report(cpu_core_time, total_elapsed)

    @timed
    def run(self, src_dir,
                end_level = sys.maxsize, include = '*', exclude = '', sort = 'n',
                filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                num_passes = 1, highpass = None, lowpass = None, backup=True):

        ''' Applies low-pass / highpass filters
        '''
        cpu_core_time = 0.0

        # validate filter values
        if not highpass and not lowpass:
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

            print('{0} media files to process, ({1} {2} each)'.format(
                                                    len(media_files), num_passes,
                                                   'passes' if num_passes > 1 else 'pass'))
            # build tasks
            tasks_params = ((media_file, backup_dir, highpass, lowpass, num_passes)
                                    for media_file, backup_dir in zip(media_files, backup_dirs))
            tasks = []
            for task_param in tasks_params:
                task = DenoiserTask(*task_param)
                tasks.append(task)

            cpu_core_time = TasksProcessor().process_tasks(tasks, serial_exec = serial_exec)
        else:
            print('No media files to process')

        return cpu_core_time








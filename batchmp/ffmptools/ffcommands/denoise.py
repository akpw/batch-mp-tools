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
    Supports multi-passes processing, e.g. 3 times for each media file
"""
import shutil, sys, os, datetime, math
from batchmp.commons.utils import temp_dir
from batchmp.ffmptools.ffrunner import FFMPRunner, FFMPRunnerTask
from batchmp.commons.taskprocessor import TasksProcessor, TaskResult
from batchmp.commons.utils import (
    timed,
    run_cmd,
    CmdProcessingError
)

class DenoiserTask(FFMPRunnerTask):
    ''' Denoise TasksProcessor task
    '''
    def __init__(self, fpath, target_dir,
                            ff_global_options, ff_other_options, preserve_metadata,
                                                        highpass, lowpass, num_passes):

        super().__init__(None, target_dir, ff_global_options, ff_other_options, preserve_metadata)
        self.fpath = fpath

        # build ffmpeg -af parameter
        if highpass and lowpass:
            af_str = 'highpass=f={0}, lowpass=f={1}'.format(highpass, lowpass)
        elif lowpass:
            af_str = 'lowpass=f={}'.format(lowpass)
        elif highpass:
            af_str = 'highpass=f={}'.format(highpass)
        else:
            raise ValueError('At least of the highpass / lowpass values must be specified')

        self.cmd = ''.join((self.cmd, ' -af "{}"'.format(af_str)))
        self.num_passes = num_passes

    def execute(self):
        ''' builds and runs Denoise command in a subprocess
        '''
        fname = os.path.basename(self.fpath)
        fname_ext = os.path.splitext(fname)[1].strip().lower()

        # ffmpeg initial input path
        fpath_input = self.fpath

        # store tags if needed
        self._store_tags()
        task_result = TaskResult()

        with temp_dir() as tmp_dir:
            # process the file in given number of passes
            for pass_cnt in range(self.num_passes):

                # compile intermediary output path
                fpath_output = ''.join((os.path.splitext(fname)[0],
                                        '_{}'.format(datetime.datetime.now().strftime("%H%M%S%f")),
                                        fname_ext))
                fpath_output = os.path.join(tmp_dir, fpath_output)

                p_in = ''.join((self._ffmpeg_input(fpath_input),
                                    self.cmd,
                                    ' "{}"'.format(fpath_output)))

                # run ffmpeg command as a subprocess
                try:
                    _, pass_elapsed = run_cmd(p_in)
                except CmdProcessingError as e:
                    task_result.add_task_step_info_msg('\nA problem while processing media file:\n\t{0}' \
                                  '\nSkipping further processing at pass {1} ...' \
                                  '\nOriginal error message:\n\t{2}' \
                                  .format(fpath_input, pass_cnt + 1, e.args[0]))
                    break
                else:
                    task_result.add_task_step_duration(pass_elapsed)

                if pass_cnt == self.num_passes - 1:
                    # the last pass, rounding up

                    # restore tags if needed
                    self._restore_tags(fpath_output)

                    # move denoised file to target dir
                    shutil.move(fpath_output, os.path.join(self.target_dir, fname))
                else:
                    # for the next pass, just make the intermediary output new input
                    fpath_input = fpath_output

        task_result.add_report_msg(self.fpath)
        return task_result

class Denoiser(FFMPRunner):
    def apply_af_filters(self, src_dir,
                            end_level = sys.maxsize, include = None, exclude = None,
                            filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                            num_passes = 1, highpass = None, lowpass = None, target_dir = None,
                            ff_global_options = None, ff_other_options = None,
                            preserve_metadata = False):

        ''' Reduce of background audio noise in media files
            via filtering out highpass / low-pass frequencies
        '''
        cpu_core_time, total_elapsed = self.run(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        quiet = quiet, num_passes = num_passes, serial_exec = serial_exec,
                                        highpass = highpass, lowpass = lowpass, target_dir = target_dir,
                                        ff_global_options = ff_global_options,
                                        ff_other_options = ff_other_options,
                                        preserve_metadata = preserve_metadata)
        # print run report
        if not quiet:
            self.run_report(cpu_core_time, total_elapsed)

    @timed
    def run(self, src_dir,
                end_level = sys.maxsize, include = None, exclude = None,
                filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                num_passes = 1, highpass = None, lowpass = None, target_dir = None,
                ff_global_options = None, ff_other_options = None,
                preserve_metadata = False):

        ''' Applies low-pass / highpass filters
        '''
        cpu_core_time = 0.0

        # validate filter values
        if not highpass and not lowpass:
            return cpu_core_time

        media_files, target_dirs = self._prepare_files(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        target_dir = target_dir, target_dir_prefix = 'denoised')

        if len(media_files) > 0:
            print('{0} media files to process, ({1} {2} each)'.format(
                                                    len(media_files), num_passes,
                                                   'passes' if num_passes > 1 else 'pass'))
            # build tasks
            tasks_params = ((media_file, target_dir_path,
                                ff_global_options, ff_other_options, preserve_metadata,
                                highpass, lowpass, num_passes)
                                    for media_file, target_dir_path in zip(media_files, target_dirs))
            tasks = []
            for task_param in tasks_params:
                task = DenoiserTask(*task_param)
                tasks.append(task)

            cpu_core_time = TasksProcessor().process_tasks(tasks, serial_exec = serial_exec, quiet = quiet)
        else:
            print('No media files to process')

        return cpu_core_time


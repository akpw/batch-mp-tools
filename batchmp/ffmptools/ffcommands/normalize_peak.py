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


""" Batch Peak Normalization of media files
"""
import shutil, sys, os, shlex
from batchmp.commons.utils import temp_dir
from batchmp.ffmptools.ffutils import FFH
from batchmp.ffmptools.ffrunner import FFMPRunner, FFMPRunnerTask, LogLevel
from batchmp.commons.taskprocessor import TaskResult
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands, FFmpegBitMaskOptions
from batchmp.commons.utils import (
    timed,
    run_cmd,
    CmdProcessingError
)

class PeakNormalizerTask(FFMPRunnerTask):
    ''' Peak Normalizer TasksProcessor task
    '''
    def __init__(self, fpath, target_dir, log_level,
                            ff_general_options, ff_other_options, preserve_metadata):

        super().__init__(fpath, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata)

    def _check_defaults(self):
        if not self.ff_other_options:
            self.ff_other_options = FFmpegCommands.CONVERT_COPY_VBR_QUALITY

        if not self.ff_general_options:
            self.ff_general_options = FFmpegBitMaskOptions.ff_general_options(
                                                          FFmpegBitMaskOptions.MAP_ALL_STREAMS)

            if self.ff_other_options == FFmpegCommands.CONVERT_COPY_VBR_QUALITY:
                self.ff_other_options += self._ff_cmd_exclude_artwork_streams()

    def ff_normalize_cmd(self, volume_gain):
        ''' Peak Normalize command builder
        '''
        return ''.join((super().ff_cmd,
                            ' -af "volume=volume={}dB"'.format(volume_gain)))
                            #'' if True else ' -c:a pcm_s16le'))

    def execute(self):
        ''' builds and runs Peak Normalization command in a subprocess
        '''
        task_result = TaskResult()

        volume_entry, task_elapsed = self._detect_volumes()
        task_result.add_task_step_duration(task_elapsed)

        if not volume_entry:
            task_result.add_task_step_info_msg('A problem analyzing volume in media file:\n\t{}' \
                                                                                .format(self.fpath))
        elif not volume_entry.max_volume:
            task_result.add_task_step_info_msg( \
                                        'Already normalized:\n\t{0}'.format(self.fpath))
            # copy source file to target dir
            shutil.copy(self.fpath, self.target_dir)

            # all well
            task_result.succeeded = True
        else:
            # store tags if needed
            self._store_tags()

            with temp_dir() as tmp_dir:
                # prepare the tmp output path
                norm_fname = os.path.basename(self.fpath)
                norm_fpath = os.path.join(tmp_dir, norm_fname)

                # build ffmpeg cmd string
                p_in = ''.join((self.ff_normalize_cmd(volume_entry.max_volume), \
                                                ' {}'.format(shlex.quote(norm_fpath))))
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
                    self._restore_tags(norm_fpath)

                    # move converted file to target dir
                    shutil.move(norm_fpath, self.target_dir)

                    # all well
                    task_result.succeeded = True

        task_result.add_report_msg(self.fpath)
        return task_result

    @timed
    def _detect_volumes(self):
        return FFH.volume_detector(self.fpath)


class PeakNormalizer(FFMPRunner):
    def peak_normalize(self, src_dir,
                            end_level = sys.maxsize, include = None, exclude = None,
                            filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                            target_dir = None, log_level = None,
                            ff_general_options = None, ff_other_options = None,
                            preserve_metadata = False):

        ''' Peak Normalization of media files
        '''
        media_files, target_dirs = self._prepare_files(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        target_dir = target_dir, target_dir_prefix = 'peak_normalized')
        # build tasks
        tasks = []
        tasks_params = [(media_file, target_dir_path, log_level,
                            ff_general_options, ff_other_options, preserve_metadata)
                                for media_file, target_dir_path in zip(media_files, target_dirs)]
        for task_param in tasks_params:
            task = PeakNormalizerTask(*task_param)
            tasks.append(task)

        # run tasks
        self.run_tasks(tasks, serial_exec = serial_exec, quiet = quiet)



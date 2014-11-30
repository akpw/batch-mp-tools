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


""" A Python module for running batch FFmpeg commands
    Supports recursive processing of media files in all subdirectoris
    Supports multi-passes processing, e.g. 3 times for each media file in source dir
    Uses Python multiprocessing to leverage available CPU cores
    Supports backing up original media in their respective folders
    Displays continuos progress
"""

import json, math
import os, sys, shutil, multiprocessing
import subprocess, datetime, shlex, tempfile

from ..commons.progressbar import progress_bar
from .ffmputils import (
    ffmpeg_installed,
    timed,
    run_cmd,
    get_media_files,
    setup_backup_dirs,
    FFmpegNotInstalled,
    FFmpegArgsError,
    CmdProcessingError
)

class FFMP(object):
    def __init__(self, src_dir = os.curdir):
        if not ffmpeg_installed():
            raise utils.FFmpegNotInstalled('\n\tLooks like ffmpeg is not installed'
                                           '\n\tCheck it out here:'
                                           ' http://www.ffmpeg.org/download.html\n')
        self.src_dir = src_dir

    # worker method used in <self.apply_af_filters>
    def _af_worker(self, task_params):
        fpath, backup_path, highpass, lowpass, num_passes = task_params
        _, fname = os.path.split(fpath)

        # meda file's extension
        fname_ext = os.path.splitext(fname)[1].strip().lower()

        # a separate tmp dir per each worker
        tmp_dir = tempfile.mkdtemp()

        # ffmpeg initial input path
        fpath_input = fpath

        # now process the file in given number of passes
        task_elapsed, output = 0.0, []
        for pass_cnt in range(num_passes):
            # compile intermediary output path
            fpath_output = ''.join((os.path.splitext(fname)[0],
                                    '_{}'.format(datetime.datetime.now().strftime("%H%M%S%f")),
                                    fname_ext))
            fpath_output = os.path.join(tmp_dir, fpath_output)

            # build ffmpeg cmd string
            if highpass and lowpass != 0:
                af_str = 'highpass=f={0}, lowpass=f={1}'.format(highpass, lowpass)
            elif lowpass != 0:
                af_str = 'lowpass=f={}'.format(lowpass)
            elif highpass != 0:
                af_str = 'highpass=f={}'.format(highpass)
            else:
                output.append('A problem while processing media file:\n\t{0}'
                              '\nAt least one of the high-pass / low-pass filter values need to be specified'
                              '\nSkipping further processing at pass {1} ...'
                              .format(fpath, pass_cnt + 1))
                break
            p_in = ''.join(('ffmpeg -i "{}"'.format(fpath_input),
                            ' -af "{}"'.format(af_str),
                            ' -loglevel "error" -n',
                            ' "{0}"'.format(fpath_output)))

            # run ffmpeg as (@utils.timed) subprocess
            try:
                _, pass_elapsed = run_cmd(p_in)
            except CmdProcessingError as e:
                output.append('A problem while processing media file:\n\t{0}'
                              '\nSkipping further processing at pass {1} ...'
                              '\nOriginal error message:\n\t{2}'
                              .format(fpath, pass_cnt + 1, e.args[0]))
                break
            else:
                task_elapsed += pass_elapsed

            # for the last pass, do some house cleaning
            if pass_cnt == num_passes - 1:
                # if applicable, backup the original file
                if backup_path != None:
                    shutil.move(fpath, backup_path)

                # move resulting output to its original name / dest
                shutil.move(fpath_output, fpath)
            else:
                # for the next pass, make the output new input
                fpath_input = fpath_output

        # almost done here, ditch the temp dir
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        # log report
        td = datetime.timedelta(seconds=task_elapsed)
        output.append('Done processing:\n {0}\n {2} {3} in {1}'.format(
                                fpath, str(td)[:10],
                                num_passes, 'passes' if num_passes > 1 else 'pass'))
        return output, task_elapsed

    @timed
    def apply_af_filters(self, num_passes=1, recursive=False, highpass=0, lowpass=0,
                                                            backup=True, quiet=False):
        ''' Applies low-pass / highpass filters
        '''
        # validate filter values
        if highpass == lowpass == 0:
            raise FFmpegArgsError('At least one of the high-pass / low-pass filter values need to be specified')

        # get the media files and prepare backup dirs
        media_files = get_media_files(src_dir = self.src_dir, recursive = recursive)

        # if backup is required, prepare the backup dirs
        if backup:
            backup_dirs = setup_backup_dirs(media_files)
        else:
            backup_dirs = [None for bd in media_files]

        tasks_done, num_tasks, cpu_core_time = 0, len(media_files), 0.0
        cpu_count = multiprocessing.cpu_count()
        print('Processing {0} media files ({1} {2} each)'.format(
                                                num_tasks, num_passes,
                                               'passes' if num_passes > 1 else 'pass'))
        print('Running with pool of {} worker processes'.format(cpu_count))

        # start showing progress
        with progress_bar() as p_bar:

            # init the pool and kick it off
            tasks_params = ((media_file, backup_dir, highpass, lowpass, num_passes)
                                for media_file, backup_dir in zip(media_files, backup_dirs))
            with multiprocessing.Pool(cpu_count) as pool:
                for res in pool.imap_unordered(self._af_worker, tasks_params):
                    if not quiet:
                        p_bar.info_msg = res[0][0]
                    cpu_core_time += res[1]
                    tasks_done += 1
                    p_bar.progress = tasks_done / num_tasks * 100

        return cpu_core_time

    def get_media_length(self, fpath):
        ''' Gets media length in seconds
        '''
        p_in = ' '.join(('ffprobe ',
                            '-loglevel "error"',
                            '-show_format',
                            '-print_format json',
                            '"{}"'.format(fpath)))
        try:
            output, _ = run_cmd(p_in)
        except CmdProcessingError as e:
            print('A problem while processing media file:\n\t"{0}"'
                  '\nOriginal error message:\n\t{1}'.format(fpath, e.args[0]))
            sys.exit()
        else:
           return math.ceil(float(json.loads(output)['format']['duration']))









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


""" Batch cue splitter
"""
import shutil, sys, os, shlex
from datetime import timedelta
from batchmp.commons.utils import temp_dir
from batchmp.ffmptools.ffrunner import FFMPRunner, LogLevel
from batchmp.commons.taskprocessor import TaskResult
from batchmp.ffmptools.ffutils import FFH
from batchmp.ffmptools.utils.cueparse import CueParser
from batchmp.tags.handlers.tagsholder import TagHolder
from batchmp.ffmptools.ffcommands.convert import ConvertorTask
from batchmp.commons.descriptors import PropertyDescriptor
from batchmp.commons.utils import (
    run_cmd,
    CmdProcessingError
)

class CueSplitTagHolder(TagHolder):
    ''' Need a few extra attributes for cue splitting
    '''
    cue_virt_fpath = PropertyDescriptor()
    time_offset = PropertyDescriptor()


class CueSplitterTask(ConvertorTask):
    ''' Cue Slit TasksProcessor task
    '''
    def __init__(self, cue_tag_holder, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata,
                                                target_format):
        # unpack relevant properties due to pickle / ultiprocessing
        self.time_offset = cue_tag_holder.time_offset
        self.duration = cue_tag_holder.length
        self.track_number = cue_tag_holder.track
        if cue_tag_holder.title:
            self.track_title = cue_tag_holder.title.replace(os.path.sep, '')

        self.albumartist = cue_tag_holder.albumartist
        self.album = cue_tag_holder.album
        self.composer = cue_tag_holder.composer
        self.comments = cue_tag_holder.comments

        super().__init__(cue_tag_holder.filepath, target_dir, log_level,
                                ff_general_options, ff_other_options, preserve_metadata, target_format)

    @property
    def ff_cmd(self):
        ''' Cue Split command builder
        '''
        return ''.join((super().ff_cmd,
                            ' -ss {}'.format(self.time_offset),
                            ' -t {}'.format(self.duration)
                            ))

    def _store_tags(self):
        if self.tag_holder:
            self.tag_holder.comments = self.comments
            self.tag_holder.title = self.track_title
            self.tag_holder.album = self.album
            self.tag_holder.composer = self.composer
            self.tag_holder.track  = self.track_number
            self.tag_holder.albumartist  = self.albumartist

    def execute(self):
        ''' builds and runs FFmpeg Conversion command in a subprocess
        '''
        # store tags if needed
        self._store_tags()

        task_result = TaskResult()

        with temp_dir() as tmp_dir:
            # prepare the tmp output path
            conv_fname = '{0:02d} {1}'.format(self.track_number, self.track_title)
            conv_fname = ''.join((conv_fname, self.target_format))
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


class CueSplitter(FFMPRunner):
    def cue_split(self, src_dir,
                    end_level = sys.maxsize, include = None, exclude = None,
                    filter_dirs = True, filter_files = True, quiet = False, serial_exec = False,
                    target_format = None,
                    target_dir = None, log_level = None,
                    ff_general_options = None, ff_other_options = None,
                    preserve_metadata = False,
                    encoding = 'utf-8'):

        ''' Converts media to specified format
        '''
        tasks = []
        if target_format:
            if not target_format.startswith('.'):
                target_format = '.{}'.format(target_format)
            target_dir_prefix = '{}'.format(target_format[1:])

            cue_tagholders, target_dirs = self._prepare_cue_data(src_dir,
                                            end_level = end_level,
                                            include = include, exclude = exclude,
                                            filter_dirs = filter_dirs, filter_files = filter_files,
                                            target_dir = target_dir, target_dir_prefix = target_dir_prefix,
                                            encoding = encoding)
            # build tasks
            tasks_params = [(cue_tag_holder, target_dir_path, log_level,
                                ff_general_options, ff_other_options, preserve_metadata,
                                target_format)
                                    for cue_tag_holder, target_dir_path in zip(cue_tagholders, target_dirs)]
            for task_param in tasks_params:
                task = CueSplitterTask(*task_param)
                tasks.append(task)

        # run tasks
        self.run_tasks(tasks, serial_exec = serial_exec, quiet = quiet)


    ## Internal helpers
    @staticmethod
    def _prepare_cue_data(src_dir, *,
                        end_level = sys.maxsize,
                        include = None, exclude = None,
                        filter_dirs = True, filter_files = True,
                        target_dir = None, target_dir_prefix = None,
                        pass_filter = None,
                        encoding = 'utf-8'):
        ''' Builds a list of target media files and their tagholder attributes corresponding to found .cue files.
            Prepares their respective target output dirs
        '''
        pass_filter = lambda fpath: fpath.endswith('.cue')
        cue_fpaths = [fpath for fpath in FFH.media_files(src_dir,
                                        end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        pass_filter = pass_filter)]

        cue_tagholders = CueSplitter._prepare_tagholders(cue_fpaths, encoding = encoding)

        target_dirs = FFMPRunner._setup_target_dirs(src_dir = src_dir,
                            target_dir = target_dir, target_dir_prefix = target_dir_prefix,
                            fpathes = [cue_tagholder.cue_virt_fpath for cue_tagholder in cue_tagholders])

        return cue_tagholders, target_dirs


    @staticmethod
    def _prepare_tagholders(cue_fpaths, encoding):
        cue_tagholders = []
        for cue_fpath in cue_fpaths:
            cue_parser = CueParser()
            cue_sheet = cue_parser.parse(cue_fpath, encoding = encoding)

            for file in cue_sheet.files:
                for track in file.tracks:
                    tag_holder = CueSplitTagHolder()

                    cue_virt_dir = os.path.dirname(cue_fpath) + os.path.sep + \
                                                        os.path.splitext(os.path.basename(cue_fpath))[0]
                    tag_holder.cue_virt_fpath = os.path.join(cue_virt_dir, file.name)
                    tag_holder.filepath = os.path.join(os.path.dirname(cue_fpath), file.name)

                    tag_holder.comments = ' '.join(cue_sheet.rem)

                    tag_holder.title = track.title if track.title else cue_sheet.title
                    tag_holder.albumartist = track.performer if track.performer else cue_sheet.performer
                    tag_holder.composer = track.songwriter if track.songwriter else cue_sheet.songwriter

                    tag_holder.track = track.number
                    tag_holder.time_offset = track.offset_in_seconds
                    tag_holder.length = track.duration_in_seconds if track.duration_in_seconds else timedelta(days = 30).total_seconds()

                    cue_tagholders.append(tag_holder)

        return cue_tagholders

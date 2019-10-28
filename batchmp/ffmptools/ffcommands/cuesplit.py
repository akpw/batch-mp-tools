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
import shutil, sys, os, shlex, re
from datetime import timedelta
from batchmp.commons.utils import temp_dir
from batchmp.ffmptools.ffrunner import FFMPRunner, LogLevel
from batchmp.commons.taskprocessor import TaskResult
from batchmp.fstools.walker import DWalker
from batchmp.ffmptools.utils.cueparse import CueParser, CueParseReadDataEncodingError
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

        # unpack relevant properties due to pickle / multiprocessing
        self.time_offset = cue_tag_holder.time_offset
        self.duration = cue_tag_holder.length

        self.track_number = cue_tag_holder.track
        self.year = cue_tag_holder.year
        self.genre = cue_tag_holder.genre
        self.track_title = cue_tag_holder.title
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
            if self.track_title:
                self.tag_holder.title = self.track_title
            if self.album:
                self.tag_holder.album = self.album
            if self.albumartist:
               self.tag_holder.albumartist  = self.albumartist
            if self.composer:
                self.tag_holder.composer = self.composer
            if self.track_number:
                self.tag_holder.track  = self.track_number
            if self.comments:
                self.tag_holder.comments = self.comments
            if self.year:
                self.tag_holder.year = self.year
            if self.genre:
                self.tag_holder.genre = self.genre


    def execute(self):
        ''' builds and runs FFmpeg Conversion command in a subprocess
        '''
        # store tags
        self._store_tags()

        task_result = TaskResult()

        with temp_dir() as tmp_dir:
            # prepare the tmp output path
            conv_fname = '{0:02d} {1}'.format(self.track_number, self.track_title)
            conv_fname = re.sub('[^\w\-_\. ]', '_', conv_fname)
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
    def cue_split(self, ff_entry_params, encoding = 'utf-8'):

        ''' Converts media to specified format
        '''
        tasks = []
        if ff_entry_params.target_format:
            if not ff_entry_params.target_format.startswith('.'):
                ff_entry_params.target_format = '.{}'.format(ff_entry_params.target_format)
            ff_entry_params.target_dir_prefix = '{}'.format(ff_entry_params.target_format[1:])

            cue_tagholders, target_dirs = self._prepare_cue_data(ff_entry_params, encoding = encoding)
            # build tasks
            tasks_params = [(cue_tag_holder, target_dir_path, ff_entry_params.log_level,
                                ff_entry_params.ff_general_options, ff_entry_params.ff_other_options, ff_entry_params.preserve_metadata,
                                ff_entry_params.target_format)
                                    for cue_tag_holder, target_dir_path in zip(cue_tagholders, target_dirs)]
            for task_param in tasks_params:
                task = CueSplitterTask(*task_param)
                tasks.append(task)

        # run tasks
        self.run_tasks(tasks, serial_exec = ff_entry_params.serial_exec, quiet = ff_entry_params.quiet)


    ## Internal helpers
    @staticmethod
    def _prepare_cue_data(ff_entry_params,                        
                        pass_filter = None,
                        encoding = 'utf-8'):
        ''' Builds a list of target media files and their tagholder attributes corresponding to found .cue files.
            Prepares their respective target output dirs
        '''
        pass_filter = lambda fpath: fpath.endswith('.cue')

        cue_fpaths = [entry.realpath for entry in DWalker.file_entries(ff_entry_params, pass_filter = pass_filter)]

        cue_tagholders = CueSplitter._prepare_tagholders(cue_fpaths, encoding = encoding)

        target_dirs = FFMPRunner._setup_target_dirs(ff_entry_params,
                        fpathes = [cue_tagholder.cue_virt_fpath for cue_tagholder in cue_tagholders])

        return cue_tagholders, target_dirs


    @staticmethod
    def _prepare_tagholders(cue_fpaths, encoding):
        cue_tagholders = []
        for cue_fpath in cue_fpaths:
            cue_parser = CueParser()
            try:
                cue_sheet = cue_parser.parse(cue_fpath, encoding = encoding)
            except CueParseReadDataEncodingError:
                print('\nUnable to read data from the "{0}" file using encoding: {1}'.format(cue_fpath, encoding))
                print('Use the \'-en\' encoding option to specify correct encoding, e.g.: -en \'latin-1\'\n')
                exit(1)

            for file in cue_sheet.files:
                for track in file.tracks:
                    tag_holder = CueSplitTagHolder()

                    cue_virt_dir = os.path.dirname(cue_fpath) + os.path.sep + \
                                                        os.path.splitext(os.path.basename(cue_fpath))[0]
                    tag_holder.cue_virt_fpath = os.path.join(cue_virt_dir, file.name)
                    tag_holder.filepath = os.path.join(os.path.dirname(cue_fpath), file.name)

                    if cue_sheet.rem:
                        for rem_item in cue_sheet.rem:
                            if not tag_holder.year:
                                match = re.match('DATE.+(\d{4})', rem_item)
                                if match:
                                    tag_holder.year = match.group(1)
                                    continue
                            if not tag_holder.genre:
                                match = re.match('GENRE\s+(.+)$', rem_item)
                                if match:
                                    tag_holder.genre = match.group(1)
                        tag_holder.comments = ', '.join(cue_sheet.rem)

                    tag_holder.title = track.title or cue_sheet.title
                    tag_holder.album = cue_sheet.title
                    tag_holder.albumartist = track.performer or cue_sheet.performer
                    tag_holder.composer = track.songwriter or cue_sheet.songwriter

                    tag_holder.track = track.number
                    tag_holder.time_offset = track.offset_in_seconds
                    tag_holder.length = track.duration_in_seconds or timedelta(days = 30).total_seconds()

                    cue_tagholders.append(tag_holder)

        return cue_tagholders


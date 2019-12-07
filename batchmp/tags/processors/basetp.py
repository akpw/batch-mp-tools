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


import sys, os, re, string
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.walker import DWalker
from batchmp.fstools.rename import DirCounters
from batchmp.tags.output.formatters import TagOutputFormatter, OutputFormatType
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.tagsholder import TagHolder
from batchmp.commons.progressbar import progress_bar, CmdProgressBarRefreshRate
from functools import partial

class BaseTagProcessor:
    ''' Base Tag Processing
    '''
    def __init__(self):
        self._handler = MutagenTagHandler() + FFmpegTagHandler()

    @property
    def handler(self):
        return self._handler

    def print_dir(self, fs_entry_params, format = None, show_stats = False):

        ''' Prints tags in selected media files
        '''
        formatter = partial(TagOutputFormatter.tags_formatter,
                                        format = format if format else OutputFormatType.COMPACT,
                                        handler = self.handler,
                                        show_stats = show_stats)

        DHandler.print_dir(fs_entry_params, 
                            formatter = formatter,
                            selected_files_description = 'media file')

    def set_tags(self, fs_entry_params, total_files, total_dirs, tag_holder = None, tag_holder_builder = None):

        ''' Set tags from tag_holder attributes
        '''
        if not tag_holder and not tag_holder_builder:
            return

        fcnt = 0
        pass_filter = lambda fpath: self.handler.can_handle(fpath)

        with progress_bar(refresh_rate = CmdProgressBarRefreshRate.FAST) as p_bar:
            p_bar.info_msg = 'Setting tags in {} media files'.format(total_files)
            for entry in DWalker.file_entries(fs_entry_params, pass_filter = pass_filter):
                if tag_holder_builder:
                    tag_holder = tag_holder_builder(entry)

                self.handler.copy_tags(tag_holder)
                self.handler.save()
                fcnt += 1

                p_bar.progress += 100 / total_files


        # print summary
        if not fs_entry_params.quiet:
            print('Set tags in {0} media file{1}'.format(fcnt, '' if fcnt == 1 else 's'))

    def set_tags_visual(self, fs_entry_params, 
                            diff_tags_only = False,
                            tag_holder = None,
                            tag_holder_builder = None, 
                            reset_tag_holder_builder = None):

        ''' Set tags from tag_holder attributes
            Visualises changes before proceeding
        '''
        if not tag_holder and not tag_holder_builder:
            return

        if fs_entry_params.quiet:
            proceed = True
            total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params)
        else:
            # visualise changes to tags and proceed if confirmed
            preformatter = partial(TagOutputFormatter.tags_formatter,
                                            handler = self.handler,
                                            show_stats = False,
                                            tag_holder = tag_holder,
                                            tag_holder_builder = tag_holder_builder,
                                            diff_tags_only = diff_tags_only)

            formatter = partial(TagOutputFormatter.tags_formatter,
                                            handler = self.handler,
                                            show_stats = False,
                                            tag_holder = tag_holder,
                                            tag_holder_builder = tag_holder_builder,
                                            show_tag_holder_values = True,
                                            diff_tags_only = diff_tags_only)

            proceed, total_files, total_dirs = DHandler.visualise_changes(fs_entry_params,
                                            preformatter = preformatter, formatter = formatter,
                                            reset_formatters = reset_tag_holder_builder,
                                            selected_files_description = 'media file')
        if proceed:
            if reset_tag_holder_builder:
                reset_tag_holder_builder()

            self.set_tags(fs_entry_params, total_files, total_dirs,
                            tag_holder = tag_holder, 
                            tag_holder_builder = tag_holder_builder)

    def copy_tags(self, fs_entry_params,  diff_tags_only = False, tag_holder_path = None):

        ''' Copies metadata (including artwork) from a tag_holder file
            then applies to all selected media files
            Visualises changes before proceeding
        '''
        if self.handler.can_handle(tag_holder_path):
            tag_holder = TagHolder()
            tag_holder.copy_tags(self.handler.tag_holder)
            self.set_tags_visual(fs_entry_params,
                                    diff_tags_only = diff_tags_only,
                                    tag_holder = tag_holder)
        else:
            print('Can not handle tags holder: {}'.format(tag_holder_path))

    def index(self, fs_entry_params,
                    diff_tags_only = False, start_from = 1):

        ''' Indexes the tracks / tracktotal tags, per media files' respective directories
            Visualises changes before proceeding
        '''

        counters = {}
        def reset_counts():
            counters.clear()

        def tag_holder_builder(entry):
            nonlocal counters

            parent_dir = os.path.dirname(entry.realpath)            
            if not counters.get(parent_dir):
                counters[parent_dir] = DirCounters(start_from, start_from, 0, 0)

            tag_holder = TagHolder()
            tag_holder.tracktotal = len(fs_entry_params.fnames)
            
            tag_holder.track = counters[parent_dir].files_cnt
            counters[parent_dir].files_cnt += 1

            return tag_holder

        self.set_tags_visual(fs_entry_params,
                        diff_tags_only = diff_tags_only,
                        tag_holder_builder = tag_holder_builder,
                        reset_tag_holder_builder = reset_counts)

    def remove_tags(self, fs_entry_params,
                        tag_fields = None,
                        diff_tags_only = False):

        ''' Removes metadata info from selected media files
            Can remove all metadata, or metadata from specified fields
            Visualises targeted changes before actual processing
        '''
        if tag_fields is None:
            # remove all tags
            tag_holder = TagHolder(copy_empty_vals = True)
        else:
            # remove specified tags
            tag_holder = TagHolder(nullable_fields = tag_fields)

        self.set_tags_visual(fs_entry_params,
                        diff_tags_only = diff_tags_only,
                        tag_holder = tag_holder)

    def replace_tags(self, fs_entry_params, 
                    diff_tags_only = False,
                    tag_fields = None, 
                    ignore_case = False, 
                    ind_str = None, replace_str = None):

        ''' RegExp-based replace in specified fields
            Visualises changes before proceeding
        '''

        if not (tag_fields and find_str):
            return

        flags = re.UNICODE
        if ignore_case:
            flags = flags | re.IGNORECASE
        p = re.compile(find_str, flags)

        def replace_transform(value):
            match = p.search(value)
            if match:
                if replace_str is not None:
                    value = p.sub(replace_str, value)
                else:
                    value = match.group()
            return value

        tag_holder = TagHolder(process_templates = False)
        for tag_field in tag_fields:
            setattr(tag_holder, tag_field, '${}'.format(tag_field))
        tag_holder.template_processor_method = replace_transform

        self.set_tags_visual(fs_entry_params, 
                                diff_tags_only = diff_tags_only, 
                                tag_holder = tag_holder)

    def capitalize_tags(self, fs_entry_params, 
                    diff_tags_only = False,
                    tag_fields = None):

        ''' Capitalizes words in specified fields
            Visualises changes before proceeding
        '''

        if not tag_fields:
            return

        def capitalize_transform(value):
            return string.capwords(value)

        tag_holder = TagHolder(process_templates = False)
        for tag_field in tag_fields:
            setattr(tag_holder, tag_field, '${}'.format(tag_field))
        tag_holder.template_processor_method = capitalize_transform

        self.set_tags_visual(fs_entry_params, 
                        diff_tags_only = diff_tags_only,
                        tag_holder = tag_holder)

    def detauch_art(self, fs_entry_params, target_dir = None):

        ''' Detauches art from selected media files
        '''

        fcnt = 0
        pass_filter = lambda fpath: self.handler.can_handle(fpath)
        for entry in DWalker.file_entries(fs_entry_params, pass_filter = pass_filter):

            if not target_dir:
                target_dir = src_dir
            else:
                os.makedirs(target_dir, exist_ok = True)

            if  self.handler.tag_holder.has_artwork:
                self.handler.detauch_art(target_dir)
                fcnt += 1

        # print summary
        if not quiet:
            print('Detauched art from {0} media entries'.format(fcnt))



# coding=utf8
## Copyright (c) 2014 Arseniy Kuznetsov
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

import sys, os
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.fsutils import DWalker
from batchmp.tags.output.formatters import TagOutputFormatter, OutputFormatType
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.tagsholder import TagHolder
from functools import partial


class BaseTagProcessor:
    ''' Base Tag Processing
    '''
    def __init__(self):
        self._handler = MutagenTagHandler() + FFmpegTagHandler()

    @property
    def handler(self):
        return self._handler

    def print_dir(self, src_dir, *, end_level = sys.maxsize,
                            include = '*', exclude = '', sort = 'n',
                            filter_dirs = True, filter_files = True,
                            flatten = False, ensure_uniq = False,
                            show_size = False, format = None, show_stats = False):
        ''' Prints tags in selected media files
        '''
        formatter = partial(TagOutputFormatter.tags_formatter,
                                        format = format if format else OutputFormatType.COMPACT,
                                        handler = self.handler,
                                        show_stats = show_stats)

        DHandler.print_dir(src_dir = src_dir, end_level = end_level,
                            include = include, exclude = exclude, sort = sort,
                            filter_dirs = filter_dirs, filter_files = filter_files,
                            flatten = flatten, ensure_uniq = ensure_uniq,
                            show_size = show_size, formatter = formatter)


    def set_tags(self, src_dir, *, end_level = sys.maxsize,
                            include = '*', exclude = '', sort = 'n',
                            filter_dirs = True, filter_files = True, quiet = False,
                            tag_holder = None, tag_holder_gen = None, copy_empty_vals = False):
        ''' Set tags from tag_holder attributes
        '''
        if not tag_holder and not tag_holder_gen:
            return

        fcnt = 0
        pass_filter = lambda fpath: self.handler.can_handle(fpath)
        for entry in fsutils.DWalker.file_entries(src_dir,
                                            end_level = end_level,
                                            include = include, exclude = exclude, sort = sort,
                                            filter_dirs = True, filter_files = True,
                                            pass_filter = pass_filter):
            if tag_holder_gen:
                try:
                    th = next(tag_holder_gen)
                except StopIteration as e:
                    pass
                else:
                    tag_holder = th

            self.handler.copy_tags(tag_holder, copy_empty_vals = copy_empty_vals)
            self.handler.save()
            fcnt += 1

        # print summary
        if not quiet:
            print('Set tags in {0} entries'.format(fcnt))


    def set_tags_visual(self, src_dir, *, end_level = sys.maxsize,
                            include = '*', exclude = '', sort = 'n',
                            filter_dirs = True, filter_files = True, quiet = False,
                            tag_holder = None, copy_empty_vals = False):
        ''' Set tags from tag_holder attributes
            Visualises changes before proceeding
        '''
        if quiet:
            proceed = True
        else:
            # diff fields
            diff_fields = []
            for field in tag_holder.taggable_fields():
                if field is 'art':
                    if tag_holder.has_artwork is not self.handler.tag_holder.has_artwork:
                        diff_fields.append(field)
                else:
                    current_val = getattr(self.handler.tag_holder, field)
                    new_val = getattr(tag_holder, field)
                    if not current_val is new_val:
                        diff_fields.append(field)

            # visualise changes to tags and proceed if confirmed
            preformatter = partial(TagOutputFormatter.tags_formatter,
                                            format = OutputFormatType.DIFF,
                                            handler = self.handler,
                                            diff_fields = diff_fields,
                                            show_stats = False)

            formatter = partial(TagOutputFormatter.tags_formatter,
                                            format = OutputFormatType.DIFF,
                                            handler = self.handler, diff_fields = diff_fields,
                                            show_stats = False,
                                            tag_holder = tag_holder, copy_empty_vals = copy_empty_vals)

            proceed = True if quiet else DHandler.visualise_changes(src_dir = src_dir,
                                            sort = sort,
                                            orig_end_level = end_level, target_end_level = end_level,
                                            include = include, exclude = exclude,
                                            filter_dirs = filter_dirs, filter_files = filter_files,
                                            preformatter = preformatter,
                                            formatter = formatter)
        if proceed:
            self.set_tags(src_dir,
                    sort = sort,
                    end_level = end_level,
                    include = include, exclude = exclude,
                    filter_dirs = filter_dirs, filter_files = filter_files,
                    tag_holder = tag_holder, quiet = quiet, copy_empty_vals = copy_empty_vals)



    def remove_tags(self, src_dir, *, end_level = sys.maxsize,
                        include = '*', exclude = '', sort = 'n',
                        filter_dirs = True, filter_files = True, quiet = False):
        ''' Removes all metadata info (including artwork) from selected media files
            Visualises changes before proceeding
        '''
        self.set_tags_visual(src_dir, end_level = end_level,
                        include = include, exclude = exclude, sort = sort,
                        filter_dirs = filter_dirs, filter_files = filter_files, quiet = quiet,
                        tag_holder = TagHolder(), copy_empty_vals = True)


    def copy_tags(self, src_dir, *, end_level = sys.maxsize,
                        include = '*', exclude = '', sort = 'n',
                        filter_dirs = True, filter_files = True, quiet = False,
                        tag_holder_path):
        ''' Copies metadata (including artwork) from a tag_holder file
            then applies it to all selected media files
            Visualises changes before proceeding
        '''
        handler_rpath = os.path.join(src_dir, tag_holder_path)
        if self.handler.can_handle(handler_rpath):
            tag_holder = TagHolder()
            tag_holder.copy_tags(self.handler.tag_holder)
            self.set_tags_visual(src_dir, end_level = end_level,
                        include = include, exclude = exclude, sort = sort,
                        filter_dirs = filter_dirs, filter_files = filter_files, quiet = quiet,
                        tag_holder = tag_holder)

    def index(self, src_dir, *, end_level = sys.maxsize,
                            include = '*', exclude = '', sort = 'n',
                            filter_dirs = True, filter_files = True, quiet = False):
        ''' Indexes the tracks / tracktotal tags
            Visualises changes before proceeding
        '''
        # Get the number of affected media files
        tracks_total = 0
        pass_filter = lambda fpath: self.handler.can_handle(fpath)
        for entry in fsutils.DWalker.file_entries(src_dir,
                                            end_level = end_level,
                                            include = include, exclude = exclude, sort = sort,
                                            filter_dirs = True, filter_files = True,
                                            pass_filter = pass_filter):
            tracks_total += 1

        def tag_holder_gen():
            for track_idx in range(1, tracks_total + 1):
                tag_holder = TagHolder()
                tag_holder.track = track_idx
                tag_holder.tracktotal = tracks_total
                yield tag_holder

        preformatter = partial(TagOutputFormatter.tags_formatter,
                                        format = OutputFormatType.TRACKS,
                                        handler = self.handler,
                                        show_stats = False)

        formatter = partial(TagOutputFormatter.tags_formatter,
                                        format = OutputFormatType.TRACKS,
                                        handler = self.handler,
                                        show_stats = False,
                                        tag_holder_gen = tag_holder_gen())

        proceed = True if quiet else DHandler.visualise_changes(src_dir = src_dir,
                    sort = sort,
                    orig_end_level = end_level, target_end_level = end_level,
                    include = include, exclude = exclude,
                    filter_dirs = filter_dirs, filter_files = filter_files,
                    preformatter = preformatter,
                    formatter = formatter)

        if proceed:
            self.set_tags(src_dir,
                    end_level = end_level,
                    include = include, exclude = exclude,
                    filter_dirs = filter_dirs, filter_files = filter_files,
                    tag_holder_gen = tag_holder_gen(), quiet = quiet)


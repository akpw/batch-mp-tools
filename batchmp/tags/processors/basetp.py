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

import sys
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.fsutils import DWalker
from batchmp.tags.utils.thfactory import TagHandlerFactory
from batchmp.tags.utils.formatters import TagOutputFormatter
from functools import partial

class BaseTagProcessor:
    def __init__(self):
        self._handlers = TagHandlerFactory()

    @property
    def handler_factory(self):
        return self._handlers

    def print_dir(self, src_dir, start_level = 0, end_level = sys.maxsize,
                            include = '*', exclude = '', sort = 'n',
                            filter_dirs = True, filter_files = True,
                            flatten = False, ensure_uniq = False,
                            show_size = False, formatter = None, show_stats = False):

        if not formatter:
            formatter = partial(TagOutputFormatter.tags_formatter,
                                            format_type = TagOutputFormatter.COMPACT,
                                            handler_factory = self.handler_factory,
                                            show_stats = show_stats)

        DHandler.print_dir(src_dir = src_dir, start_level = start_level, end_level = end_level,
                            include = include, exclude = exclude, sort = sort,
                            filter_dirs = filter_dirs, filter_files = filter_files,
                            flatten = flatten, ensure_uniq = ensure_uniq,
                            show_size = show_size, formatter = formatter)


    def set_tags(self, src_dir, start_level = 0, end_level = sys.maxsize,
                            include = '*', exclude = '',
                            filter_dirs = True, filter_files = True,
                            tag_holder = None, quiet = False):
        """ Set tags from tag_holder attributes
        """
        if not tag_holder:
            return

        fcnt = 0
        for entry in DWalker.entries(src_dir = src_dir,
                                    start_level = start_level, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files):

            if entry.type in (DWalker.ENTRY_TYPE_ROOT, DWalker.ENTRY_TYPE_DIR):
                continue

            handler = self.handler_factory.handler(entry.realpath)
            if not handler:
                continue
            else:
                handler.copy_fields(tag_holder)
                handler.save()
                fcnt += 1

        # print summary
        if not quiet:
            print('Set tags in {0} entries'.format(fcnt))



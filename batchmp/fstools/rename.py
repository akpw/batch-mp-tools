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

import os, sys, fnmatch, re, shutil
import datetime
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.fsutils import FSH, DWalker

class Renamer(object):
    """ Renamer
    """

    @staticmethod
    def add_text(src_dir, as_prefix=False):
        """ add text to names
        """
        pass

    @staticmethod
    def replace_text(src_dir):
        """ replaces text
        """
        pass

    @staticmethod
    def add_index(src_dir, as_prefix = True, start = 1, min_digits = 0):
        """ add index
        """
        pass

    @staticmethod
    def add_date(src_dir, as_prefix = False, join_str = '_', format = '%Y-%m-%d',
                                max_depth = sys.maxsize, include = '*', exclude = '',
                                filter_dirs = True, filter_files = True,
                                include_dirs = False, include_files = True):
        """ adds current date
        """
        addition = datetime.datetime.now().strftime(format)
        join_str = str(join_str)

        print('Current source directory:')
        DHandler.print_dir(src_dir = src_dir, max_depth = max_depth,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files)

        def add_date_transform(entry):
            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                return entry.basename
            if os.path.isdir(entry.realpath) and not include_dirs:
                return entry.basename
            if os.path.isfile(entry.realpath) and not include_files:
                return entry.basename

            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                return join_str.join((entry.basename, addition))

        print('\nTargeted after rename:')
        DHandler.print_dir(src_dir = src_dir, max_depth = max_depth,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_date_transform)

        if FSH.get_user_input():
            DWalker.rename_entries(src_dir = src_dir, max_depth = max_depth,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_date_transform)


    @staticmethod
    def remove_text(src_dir):
        pass


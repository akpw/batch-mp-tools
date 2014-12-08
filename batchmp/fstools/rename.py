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
import datetime, copy
from collections import namedtuple
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
    def add_index(src_dir, as_prefix = False, join_str = '_',
                            start_from = 1, min_digits = 1,
                            end_level = 0, include = '*', exclude = '',
                            filter_dirs = True, filter_files = True,
                            include_dirs = False, include_files = True):
        """ adds index
        """
        try:
            start_from = int(start_from)
        except ValueError:
            start_from = 1

        join_str = str(join_str)

        def num_digits(n):
            n_d = 1
            while (int(n/(10**n_d)) > 0):
                n_d += 1
            return max(min_digits, n_d)

        # for each level to index,
        # need to know number of digits for formatting,
        # as well as current index counters
        levels = []
        LevelInfo = namedtuple('LevelInfo', ['dirs_info', 'files_info'])
        EntryInfo = namedtuple('EntryInfo', ['num_digits', 'counter'])
        for level in range(0, end_level + 1):
            fcnt, dcnt, _ = DHandler.dir_stats(src_dir = src_dir,
                                            start_level = level, end_level = level,
                                            include = include, exclude = exclude,
                                            filter_dirs = filter_dirs, filter_files = filter_files,
                                            include_size = False)
            dir_entry_info = EntryInfo(num_digits(dcnt), 0)
            files_entry_info = EntryInfo(num_digits(fcnt), 0)
            levels.append(LevelInfo(dir_entry_info, files_entry_info))

        # copy levels info for subsequent pass
        levels_copy = copy.deepcopy(levels)

        print('Current source directory:')
        DHandler.print_dir(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files)

        def add_index_transform(entry):
            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                return entry.basename

            level = FSH.level_from_root(src_dir, entry.realpath)
            dirs_info = levels[level-1].dirs_info
            files_info = levels[level-1].files_info

            if entry.type == DWalker.ENTRY_TYPE_DIR:
                if not include_dirs:
                    return entry.basename
                else:
                    dir_cnt = dirs_info.counter + 1
                    num_digits = dirs_info.num_digits
                    addition = str(dir_cnt).zfill(num_digits)

                    # update the entry for level
                    levels[level-1] = LevelInfo(EntryInfo(num_digits, dir_cnt), files_info)

            elif entry.type == DWalker.ENTRY_TYPE_FILE:
                if not include_files:
                    return entry.basename
                else:
                    files_cnt = files_info.counter + 1
                    num_digits = files_info.num_digits
                    addition = str(files_cnt).zfill(num_digits)

                    # update the entry for level
                    levels[level-1] = LevelInfo(dirs_info, EntryInfo(num_digits, files_cnt))

            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        print('\nTargeted after rename:')
        DHandler.print_dir(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_index_transform)

        if FSH.get_user_input():
            levels = levels_copy
            DHandler.rename_entries(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_index_transform)


    @staticmethod
    def add_date(src_dir, as_prefix = False, join_str = '_', format = '%Y-%m-%d',
                                end_level = 0, include = '*', exclude = '',
                                filter_dirs = True, filter_files = True,
                                include_dirs = False, include_files = True):
        """ adds current date
        """
        addition = datetime.datetime.now().strftime(format)
        join_str = str(join_str)

        print('Current source directory:')
        DHandler.print_dir(src_dir = src_dir, end_level = end_level,
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
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        print('\nTargeted after rename:')
        DHandler.print_dir(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_date_transform)

        if FSH.get_user_input():
            DHandler.rename_entries(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_date_transform)


    @staticmethod
    def remove_text(src_dir):
        pass

if __name__ == '__main__':
    src_dir = '/Users/AKPower/_Dev/GitHub/batch-mp-tools/tests/fs/data'
    Renamer.add_index(src_dir, end_level=6, include = '[!.]*',
                      as_prefix = True, include_dirs = True, min_digits = 2)

    #Renamer.add_date(src_dir)

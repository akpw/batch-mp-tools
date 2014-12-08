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

        files_cnt = dirs_cnt = start_from
        total_files, total_dirs, _ = DHandler.dir_stats(src_dir = src_dir)
        parent_dir = os.path.realpath(src_dir)

        print('Current source directory:')
        DHandler.print_dir(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files)

        dirs_info = {}
        DirInfo = namedtuple('DirInfo', ['total_files', 'total_dirs', 'files_cnt', 'dirs_cnt'])
        def get_dir_info(dirname):
            if not dirname in dirs_info.keys():
                total_files, total_dirs, _ = DHandler.dir_stats(src_dir = dirname)
                dir_info = DirInfo(total_files, total_dirs, start_from, start_from)
                dirs_info[dirname] = dir_info

            return dirs_info[dirname]

        def add_index_transform(entry):
            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                return entry.basename

            parent_dir = os.path.dirname(entry.realpath)
            dir_info = get_dir_info(parent_dir)

            if entry.type == DWalker.ENTRY_TYPE_DIR:
                if not include_dirs:
                    return entry.basename
                else:
                    addition = str(dir_info.dirs_cnt).zfill(num_digits(dir_info.total_dirs))

                    #need to update the dirs counter
                    dirs_info[parent_dir] = DirInfo(dir_info.total_files, dir_info.total_dirs,
                                                        dir_info.files_cnt, dir_info.dirs_cnt + 1)
            # files
            elif entry.type == DWalker.ENTRY_TYPE_FILE:
                if not include_files:
                    return entry.basename
                else:
                    addition = str(dir_info.files_cnt).zfill(num_digits(dir_info.total_files))

                    #need to update the dirs counter
                    dirs_info[parent_dir] = DirInfo(dir_info.total_files, dir_info.total_dirs,
                                                        dir_info.files_cnt + 1, dir_info.dirs_cnt)

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
            # reset counters
            for parent_dir in dirs_info.keys():
                dir_info = get_dir_info(parent_dir)
                dirs_info[parent_dir] = DirInfo(dir_info.total_files, dir_info.total_dirs,
                                                        start_from, start_from)
            # ...and rename
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
                      as_prefix = True, join_str = ' ',include_dirs = True, min_digits = 2)

    #Renamer.add_date(src_dir)

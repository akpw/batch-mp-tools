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


class DirsIndexInfo:
    ''' A helper class,
        indexing info for nested directories
    '''
    DirStats = namedtuple('DirStats',
             ['total_files', 'total_dirs', 'files_cnt', 'dirs_cnt'])

    def __init__(self, start_from, min_digits):
        self.dirs_info = {}
        self.start_from = start_from
        self.min_digits = min_digits

    def get_dir_stats(self, dirname):
        if not dirname in self.dirs_info.keys():
            total_files, total_dirs, _ = DHandler.dir_stats(src_dir = dirname, end_level = 0)
            dir_info = self.DirStats(total_files, total_dirs, self.start_from, self.start_from)
            self.dirs_info[dirname] = dir_info
        return self.dirs_info[dirname]

    def update_dir_stats(self, dirname, dir_stats):
        if dirname in self.dirs_info.keys():
            self.dirs_info[dirname] = dir_stats

    def reset_counters(self):
        for key in self.dirs_info.keys():
            dir_info = self.get_dir_stats(key)
            self.dirs_info[key] = self.DirStats(dir_info.total_files, dir_info.total_dirs,
                                                                    self.start_from, self.start_from)
    def num_digits(self, n):
        n_d = 1
        while (int(n/(10**n_d)) > 0):
            n_d += 1
        return max(self.min_digits, n_d)


class Renamer(object):
    """ Renames FS entries
    """
    @staticmethod
    def add_index(src_dir, as_prefix = False, join_str = '_',
                            start_from = 1, min_digits = 1,
                            end_level = 0, sort = 'n',
                            include = '*', exclude = '',
                            filter_dirs = True, filter_files = True,
                            include_dirs = False, include_files = True, quiet = False):
        """ adds indexing
            automatically figures out right number of min_digits
        """
        try:
            start_from = int(start_from)
        except ValueError:
            start_from = 1

        join_str = str(join_str)
        dir_info = DirsIndexInfo(start_from, min_digits)

        def add_index_transform(entry):
            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                return entry.basename

            parent_dir = os.path.dirname(entry.realpath)
            dir_stats = dir_info.get_dir_stats(parent_dir)

            if entry.type == DWalker.ENTRY_TYPE_DIR:
                if not include_dirs:
                    return entry.basename
                else:
                    addition = str(dir_stats.dirs_cnt).zfill(dir_info.num_digits(dir_stats.total_dirs))

                    # need to update the dirs counter
                    dir_stats = dir_info.DirStats(dir_stats.total_files, dir_stats.total_dirs,
                                                        dir_stats.files_cnt, dir_stats.dirs_cnt + 1)
                    dir_info.update_dir_stats(parent_dir, dir_stats)

            # files
            elif entry.type == DWalker.ENTRY_TYPE_FILE:
                if not include_files:
                    return entry.basename
                else:
                    addition = str(dir_stats.files_cnt).zfill(dir_info.num_digits(dir_stats.total_files))

                    # need to update the files counter
                    dir_stats = dir_info.DirStats(dir_stats.total_files, dir_stats.total_dirs,
                                                        dir_stats.files_cnt + 1, dir_stats.dirs_cnt)
                    dir_info.update_dir_stats(parent_dir, dir_stats)

            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        # visualise changes and proceed if confirmed
        proceed = True if quiet else DHandler.visualise_changes(src_dir = src_dir, sort = sort,
                                    orig_end_level = end_level, target_end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_index_transform)
        if proceed:
            # reset counters
            dir_info.reset_counters()

            # ...and rename
            DHandler.rename_entries(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_index_transform, quiet = quiet)


    @staticmethod
    def add_date(src_dir, as_prefix = False, join_str = '_', format = '%Y-%m-%d',
                                end_level = 0, sort = 'n',
                                include = '*', exclude = '',
                                filter_dirs = True, filter_files = True,
                                include_dirs = False, include_files = True, quiet = False):
        """ adds current date
        """
        addition = datetime.datetime.now().strftime(format)
        join_str = str(join_str)

        def add_date_transform(entry):
            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == DWalker.ENTRY_TYPE_DIR and not include_dirs:
                return entry.basename
            if entry.type == DWalker.ENTRY_TYPE_FILE and not include_files:
                return entry.basename

            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        # visualise changes and proceed if confirmed
        proceed = True if quiet else DHandler.visualise_changes(src_dir = src_dir, sort = sort,
                                    orig_end_level = end_level, target_end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_date_transform)
        if proceed:
            DHandler.rename_entries(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_date_transform, quiet = quiet)


    @staticmethod
    def add_text(src_dir, text,
                    as_prefix = False, join_str = ' ',
                    end_level = 0, sort = 'n',
                    include = '*', exclude = '',
                    filter_dirs = True, filter_files = True,
                    include_dirs = False, include_files = True, quiet = False):
        """ adds text
        """
        addition = text
        join_str = str(join_str)

        def add_text_transform(entry):
            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == DWalker.ENTRY_TYPE_DIR and not include_dirs:
                return entry.basename
            if entry.type == DWalker.ENTRY_TYPE_FILE and not include_files:
                return entry.basename

            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        # visualise changes and proceed if confirmed
        proceed = True if quiet else DHandler.visualise_changes(src_dir = src_dir, sort = sort,
                                    orig_end_level = end_level, target_end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_text_transform)
        if proceed:
            DHandler.rename_entries(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_text_transform, quiet = quiet)

    @staticmethod
    def remove_n_characters(src_dir, sort = 'n',
                            num_chars = 0, from_head = True,
                            end_level = 0, include = '*', exclude = '',
                            filter_dirs = True, filter_files = True,
                            include_dirs = False, include_files = True, quiet = False):
        """ removes n first characters
        """
        num_chars = abs(num_chars)

        def remove_n_chars_transform(entry):
            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == DWalker.ENTRY_TYPE_DIR and not include_dirs:
                return entry.basename
            if entry.type == DWalker.ENTRY_TYPE_FILE and not include_files:
                return entry.basename

            name_base, name_ext = os.path.splitext(entry.basename)
            if from_head:
                name_base = name_base[num_chars:]
            else:
                name_base = name_base[:-num_chars]
            return ''.join((name_base, name_ext))

        # visualise changes and proceed if confirmed
        proceed = True if quiet else DHandler.visualise_changes(src_dir = src_dir, sort = sort,
                                    orig_end_level = end_level, target_end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = remove_n_chars_transform)
        if proceed:
            DHandler.rename_entries(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = remove_n_chars_transform, quiet = quiet)

    @staticmethod
    def replace(src_dir,
                    find_str, replace_str, case_insensitive=False,
                    end_level = 0, sort = 'n',
                    include = '*', exclude = '',
                    filter_dirs = True, filter_files = True,
                    include_dirs = False, include_files = True, quiet = False):
        """ replaces text
        """
        flags = re.UNICODE
        if case_insensitive:
            flags = flags | re.IGNORECASE
        p = re.compile(find_str, flags)

        def add_replace_transform(entry):
            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == DWalker.ENTRY_TYPE_DIR and not include_dirs:
                return entry.basename
            if entry.type == DWalker.ENTRY_TYPE_FILE and not include_files:
                return entry.basename

            match = p.search(entry.basename)
            if match:
                name_base, name_ext = os.path.splitext(entry.basename)
                if replace_str:
                    name_base = p.sub(replace_str, name_base)
                else:
                    name_base = match.group()
                return '{0}{1}'.format(name_base, name_ext)
            else:
                return entry.basename

        # visualise changes and proceed if confirmed
        proceed = True if quiet else DHandler.visualise_changes(src_dir = src_dir, sort = sort,
                                    orig_end_level = end_level, target_end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_replace_transform)
        if proceed:
            DHandler.rename_entries(src_dir = src_dir, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = add_replace_transform, quiet = quiet)



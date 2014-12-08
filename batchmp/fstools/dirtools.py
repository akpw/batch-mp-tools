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


import os, sys, shutil
import mutagen
from collections import namedtuple
from batchmp.fstools.fsutils import DWalker, FSH

class DHandler:
    @staticmethod
    def print_dir(src_dir, start_level = 0, end_level = sys.maxsize,
                            include = '*', exclude = '', sort = 'n',
                            filter_dirs = True, filter_files = True,
                            flatten = False, ensure_uniq = False,
                            show_size = False, formatter = lambda entry: entry.basename):
        """ Prints content of given directory
            supports recursion to end_level
            supports flattening folders beyond end_level
            allows for include / exclude patterns (Unix style)
            sorting:
                's' / 'sd': by size / by size descending
                'n' / 'nd': by name / by name descending
            formatter: additional display name processing, as supplied by the caller
        """
        if not os.path.exists(src_dir):
            raise ValueError('Not a valid path')

        # print the dir tree
        fcnt = dcnt = 0
        size, total_size = '', 0
        for entry in DWalker.entries(src_dir = src_dir,
                                    start_level = start_level, end_level = end_level,
                                    include = include, exclude = exclude, sort = sort,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    flatten = flatten, ensure_uniq = ensure_uniq):

            if entry.type == DWalker.ENTRY_TYPE_FILE:
                fcnt += 1
                if show_size:
                    fsize = os.path.getsize(entry.realpath)
                    size = ' {} '.format(file_size(fsize))
                    total_size += fsize
            elif entry.type == DWalker.ENTRY_TYPE_DIR:
                dcnt += 1
            print('{0}{1}{2}'.format(entry.indent, size, formatter(entry)))

        # print summary
        print('{0} files, {1} folders'.format(fcnt, dcnt))
        if show_size:
            print('Total size: {}'.format(file_size(total_size)))

    @staticmethod
    def dir_stats(src_dir, start_level = 0, end_level = sys.maxsize, flatten = False,
                        include = '*', exclude = '',
                        filter_dirs = True, filter_files = True,
                        include_size = True):
        """ Returns base stats for given directory
        """
        if not os.path.exists(src_dir):
            raise ValueError('Not a valid path')

        # count number of files, folders, and their total size
        fcnt = dcnt = total_size = 0
        for entry in DWalker.entries(src_dir = src_dir,
                                        start_level = start_level, end_level = end_level,
                                        flatten=flatten, include=include, exclude=exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files):

            if entry.type == DWalker.ENTRY_TYPE_FILE:
                fcnt += 1
            elif entry.type == DWalker.ENTRY_TYPE_DIR:
                if FSH.level_from_root(src_dir, entry.realpath) > start_level:
                    dcnt += 1

            if include_size:
                total_size += os.path.getsize(entry.realpath)

        return fcnt, dcnt, total_size

    @staticmethod
    def rename_entries(src_dir, start_level = 0, end_level = sys.maxsize,
                            include = '*', exclude = '',
                            filter_dirs = True, filter_files = True,
                            formatter = None, quiet = False):
        """ Renames directory entries via applying formatter function supplied by the caller
        """
        if not formatter:
            return

        fcnt = dcnt = 0
        DirEntry = namedtuple('DirEntry', ['orig_path', 'target_path'])
        dir_entries = []
        for entry in DWalker.entries(src_dir = src_dir,
                                    start_level = start_level, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files):

            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                continue

            target_name = formatter(entry)
            if target_name == entry.basename:
                continue

            target_path = os.path.join(os.path.dirname(entry.realpath), target_name)

            if entry.type == DWalker.ENTRY_TYPE_DIR:
                # for dirs, need to postpone rename
                dcnt += 1
                dir_entries.append(DirEntry(entry.realpath, target_path))

            elif entry.type == DWalker.ENTRY_TYPE_FILE:
                # for files, just rename
                fcnt += 1
                shutil.move(entry.realpath, target_path)

        #rename the dirs
        for dir_entry in reversed(dir_entries):
            shutil.move(dir_entry.orig_path, dir_entry.target_path)

        # print summary
        if not quiet:
            print('Renamed: {0} files, {1} folders'.format(fcnt, dcnt))

    @staticmethod
    def flatten_folders(src_dir, target_level = sys.maxsize,
                                    include = '*', exclude = '',
                                    filter_dirs = True, filter_files = True):

        print('Current source directory structure:')
        DHandler.print_dir(src_dir = src_dir,
                            include = include, exclude = exclude,
                            filter_dirs = filter_dirs, filter_files = filter_files)

        print ('\nTargeted new structure:')
        DHandler.print_dir(src_dir = src_dir, end_level = target_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    flatten = True, ensure_uniq = True)


        if FSH.get_user_input():
            # OK to go
            DWalker.flatten_folders(src_dir = src_dir, target_level = target_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files)

            # remove excessive folders
            FSH.remove_empty_folders_below_level(src_dir, target_level)

        print('\nDone')

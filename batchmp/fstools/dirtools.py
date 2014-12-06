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


import os, sys
import mutagen
from .fsutils import DWalker, FSH

class DHandler:
    @staticmethod
    def print_dir(src_dir, start_level = 0, max_depth = sys.maxsize,
                            include = '*', exclude = '', sort = 'n',
                            filter_dirs = True, filter_files = True,
                            flatten = False, ensure_uniq = False,
                            show_size = False, formatter = lambda entry: entry.basename):
        """ Prints content of given directory
            supports recursion to max_depth level
            supports flattening folders beyond max_depth (making their files show at max_depth levels)
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
                                    start_level = start_level, max_depth = max_depth,
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
    def flatten_folders(src_dir, target_depth = sys.maxsize,
                                    include = '*', exclude = '',
                                    filter_dirs = True, filter_files = True):

        print('Current source directory structure:')
        DHandler.print_dir(src_dir = src_dir,
                            include = include, exclude = exclude,
                            filter_dirs = filter_dirs, filter_files = filter_files)

        print ('\nTargeted new structure:')
        DHandler.print_dir(src_dir = src_dir, max_depth = target_depth,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    flatten = True, ensure_uniq = True)


        if FSH.get_user_input():
            # OK to go
            DWalker.flatten_folders(src_dir = src_dir, target_depth = target_depth,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files)

            # remove excessive folders
            FSH.remove_empty_folders_below_target_depth(src_dir, target_depth)

        print('\nDone')

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
from distutils.util import strtobool
from .fsutils import DWalker, FSH

class DHandler:
    @staticmethod
    def dir_stats(src_dir, max_depth = sys.maxsize, flatten = False,
                        include = '*', exclude = '', include_size = False):
        """ Returns base stats for given directory
        """
        if not os.path.exists(src_dir):
            raise ValueError('Not a valid path')

        # count number of files, folders, and their total size
        fcnt = dcnt = total_size = 0
        for entry in DWalker.entries(src_dir = src_dir, max_depth = max_depth,
                                         flatten=flatten, include=include, exclude=exclude):
            if entry.type == DWalker.ENTRY_TYPE_FILE:
                fcnt += 1
            else:
                dcnt += 1

            if include_size:
                total_size += os.path.getsize(entry.realpath)

        return fcnt, dcnt, total_size

    @staticmethod
    def print_dir(src_dir, start_level = 0, max_depth = sys.maxsize,
                            include = '*', exclude = '', sort = 'n',
                            flatten = False, ensure_uniq = False,
                            show_size = False):
        """ Prints content of given directory
            supports recursion to max_depth level
            supports flattening folders beyond max_depth (making their files show at max_depth levels)
            allows for include / exclude patterns (Unix style)
            sorting:
                's' / 'sd': by size / by size descending
                'n' / 'nd': by name / by name descending
        """
        if not os.path.exists(src_dir):
            raise ValueError('Not a valid path')

        # print the dir tree
        fcnt = dcnt = 0
        size, total_size = '', 0
        for entry in DWalker.entries(src_dir = src_dir,
                                    start_level = start_level, max_depth = max_depth,
                                    include = include, exclude = exclude, sort = sort,
                                    flatten = flatten, ensure_uniq = ensure_uniq):

            if entry.type == DWalker.ENTRY_TYPE_FILE:
                fcnt += 1
                if show_size:
                    fsize = os.path.getsize(entry.realpath)
                    size = ' {} '.format(file_size(fsize))
                    total_size += fsize
            else:
                dcnt += 1
            print('{0}{1}{2}'.format(entry.indent, size, entry.basename))

        # print summary
        print('\n{0} files in {1} folders'.format(fcnt, dcnt))
        if show_size:
            print('Total size: {}'.format(file_size(total_size)))


    @staticmethod
    def flatten_folders(src_dir, target_depth = 2):

        print('Current source directory structure:')
        DHandler.print_dir(src_dir = src_dir)

        print ('\nTargeted new structure:')
        DHandler.print_dir(src_dir = src_dir, max_depth = target_depth,
                                            flatten = True, ensure_uniq = True)

        answer = input('\nProceed? [y/n]: ')
        try:
            answer = True if strtobool(answer) else False
        except ValueError:
            print('Not confirmative, going to quit')
            sys.exit(1)

        if not answer:
            print('Not confirmed, exiting')
        else:
            # OK to go
            DWalker.flatten_folders(src_dir = src_dir, target_depth = target_depth)

            # remove excessive folders
            FSH.remove_empty_folders_below_target_depth(src_dir, target_depth)

        print('\nDone')

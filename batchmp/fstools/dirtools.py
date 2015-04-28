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


import os, sys
from collections import namedtuple, Iterable
from distutils.util import strtobool
from batchmp.fstools.fsutils import DWalker, FSH


class DHandler:
    ''' FS Directory level utilities
    '''
    @staticmethod
    def print_dir(src_dir, *,
                        start_level = 0, end_level = sys.maxsize,
                        include = None, exclude = None,
                        sort = None, nested_indent = None,
                        filter_dirs = True, filter_files = True,
                        flatten = False, ensure_uniq = False,
                        show_size = False, formatter = None, selected_files_description = None):
        """ Prints content of given directory
            Supports additional display name processing via formatter supplied by the caller
        """
        if not os.path.exists(src_dir):
            raise ValueError('Not a valid path')

        if formatter is None:
            formatter = lambda entry: entry.basename

        if selected_files_description is None:
            selected_files_description = 'file'

        # print the dir tree
        fcnt = dcnt = 0
        total_size = 0
        for entry in DWalker.entries(src_dir = src_dir,
                                    start_level = start_level, end_level = end_level,
                                    include = include, exclude = exclude,
                                    sort = sort, nested_indent = nested_indent,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    flatten = flatten, ensure_uniq = ensure_uniq):
            # get formatted output
            formatted_output = ''
            if isinstance(formatter, Iterable):
                for chained_formatter in formatter:
                    chained_formatter_output = chained_formatter(entry)
                    formatted_output = '{0}{1}'.format(
                            formatted_output if formatted_output else '',
                            chained_formatter_output if chained_formatter_output else '')
            else:
                formatted_output = formatter(entry)

            if formatted_output:
                size = ''
                if entry.type == DWalker.ENTRY_TYPE_FILE:
                    fcnt += 1
                    if show_size:
                        fsize = os.path.getsize(entry.realpath)
                        size = ' {} '.format(FSH.fs_size(fsize))
                        total_size += fsize
                elif entry.type == DWalker.ENTRY_TYPE_DIR:
                    dcnt += 1
                    if show_size:
                        dsize = FSH.dir_size(entry.realpath)
                        size = ' {} '.format(FSH.fs_size(dsize))

                print('{0}{1}{2}'.format(entry.indent, size, formatted_output))

        # print summary
        print('{0} {1}{2}, {3} folder{4}'.format(fcnt,
                                                    selected_files_description, '' if fcnt == 1 else 's',
                                                    dcnt, '' if dcnt == 1 else 's'))
        if show_size:
            print('Total selected files size: {}'.format(FSH.fs_size(total_size)))

        return fcnt, dcnt

    @staticmethod
    def dir_stats(src_dir, *,
                        start_level = 0, end_level = sys.maxsize, flatten = False,
                        include = None, exclude = None,
                        filter_dirs = True, filter_files = True,
                        include_size = False,
                        file_pass_filter = None, dir_pass_filter = None):
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
                if file_pass_filter and (not file_pass_filter(entry.realpath)):
                    continue
                fcnt += 1
            elif entry.type == DWalker.ENTRY_TYPE_DIR:
                if dir_pass_filter and (not dir_pass_filter(entry.realpath)):
                    continue
                if FSH.level_from_root(src_dir, entry.realpath) > start_level:
                    dcnt += 1

            if include_size:
                total_size += os.path.getsize(entry.realpath)

        return fcnt, dcnt, total_size

    @staticmethod
    def get_user_input(quiet = False):
        ''' Displays confirmation promt and gathers users' input
        '''
        answer = input('\nProceed? [y/n]: ')
        try:
            answer = True if strtobool(answer) else False
        except ValueError:
            print('Not confirmative, exiting')
            return False

        if not quiet:
            if answer:
                print('Confirmed, processing...')
            else:
                print('Not confirmed, exiting')

        return answer

    @staticmethod
    def visualise_changes(src_dir, *,
                                before_msg = 'Current source directory:',
                                after_msg = 'Targeted after processing:',
                                orig_end_level = sys.maxsize, target_end_level = 0,
                                include = None, exclude = None,
                                sort = None, nested_indent = None,
                                filter_dirs = True, filter_files = True,
                                include_dirs = False, include_files = True,
                                flatten = False, ensure_uniq = False,
                                preformatter = None, formatter = None, reset_formatters = None,
                                display_current = True, selected_files_description = None):

        ''' Displays targeted changes and gets users' confirmation on futher processing
        '''

        if display_current:
            print(before_msg)
            DHandler.print_dir(src_dir = src_dir,
                                    end_level = orig_end_level,
                                    sort = sort, nested_indent = nested_indent,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    formatter = preformatter,
                                    selected_files_description = selected_files_description)
            if reset_formatters:
                reset_formatters()
            print()

        print(after_msg)
        fcnt, dcnt = DHandler.print_dir(src_dir = src_dir,
                                end_level = target_end_level,
                                sort = sort, nested_indent = nested_indent,
                                include = include, exclude = exclude,
                                filter_dirs = filter_dirs, filter_files = filter_files,
                                flatten = flatten, ensure_uniq = ensure_uniq,
                                formatter = formatter,
                                selected_files_description = selected_files_description)
        if fcnt == dcnt == 0:
            print ('Nothing to process')
            return False
        else:
            return DHandler.get_user_input()

    @staticmethod
    def flatten_folders(src_dir, *,
                                target_level = sys.maxsize, end_level = sys.maxsize,
                                sort = None, nested_indent = None,
                                include = None, exclude = None,
                                filter_dirs = True, filter_files = True,
                                remove_folders = True, remove_non_empty_folders = False,
                                display_current = True, quiet = False):

        ''' Flatten all folders below target level, moving the files up at the target level
        '''

        if end_level < target_level:
            end_level = target_level

        proceed = True if quiet else DHandler.visualise_changes(src_dir = src_dir,
                                        orig_end_level = end_level,
                                        target_end_level = target_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        sort = sort, nested_indent = nested_indent,
                                        flatten = True, ensure_uniq = True, display_current = display_current)
        if proceed:
            # OK to go
            flattened_dirs_cnt = flattened_files_cnt = 0
            for entry in DWalker.entries(src_dir = src_dir,
                                        start_level = target_level, end_level=target_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                        flatten = True, ensure_uniq = True):

                if entry.type in (DWalker.ENTRY_TYPE_DIR, DWalker.ENTRY_TYPE_ROOT):
                    if FSH.level_from_root(src_dir, entry.realpath) == target_level:
                        target_dir_path = entry.realpath
                else:
                    # files
                    if FSH.level_from_root(src_dir, entry.realpath) - 1 > target_level:
                        target_fpath = os.path.join(target_dir_path, entry.basename)
                        if FSH.move_FS_entry(entry.realpath, target_fpath):
                            flattened_files_cnt += 1

            # remove excessive folders
            if remove_folders:
                flattened_dirs_cnt = FSH.remove_folders_below_target_level(src_dir,
                                                       target_level = target_level,
                                                       empty_only = not remove_non_empty_folders)
            # print summary
            if not quiet:
                print('Flattened: {0} files, {1} folders'.format(flattened_files_cnt, flattened_dirs_cnt))

        if not quiet:
            print('\nDone')

    @staticmethod
    def rename_entries(src_dir, *,
                            start_level = 0, end_level = sys.maxsize,
                            include = None, exclude = None,
                            filter_dirs = True, filter_files = True,
                            formatter = None, quiet = False, check_unique = True):

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
                # for dirs, need to postpone
                dir_entries.append(DirEntry(entry.realpath, target_path))

            elif entry.type == DWalker.ENTRY_TYPE_FILE:
                # for files, just rename
                if FSH.move_FS_entry(entry.realpath, target_path, check_unique = check_unique):
                    fcnt += 1

        #rename the dirs
        for dir_entry in reversed(dir_entries):
            if FSH.move_FS_entry(dir_entry.orig_path, dir_entry.target_path, check_unique = check_unique):
                dcnt += 1

        # print summary
        if not quiet:
            print('Renamed: {0} files, {1} folders'.format(fcnt, dcnt))

    @staticmethod
    def remove_entries(src_dir, *,
                            start_level = 0, end_level = sys.maxsize,
                            include = None, exclude = None,
                            filter_dirs = True, filter_files = True,
                            formatter = None, quiet = False):

        """ Removes entries with formatter function supplied by the caller
        """
        if not formatter:
            return

        fcnt = dcnt = 0
        dir_entries = []
        for entry in DWalker.entries(src_dir = src_dir,
                                    start_level = start_level, end_level = end_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files):

            if entry.type == DWalker.ENTRY_TYPE_ROOT:
                continue

            if formatter(entry) is None:
                continue

            if entry.type == DWalker.ENTRY_TYPE_DIR:
                # for dirs, need to postpone
                dir_entries.append(entry.realpath)

            elif entry.type == DWalker.ENTRY_TYPE_FILE:
                # for files, OK to remove now
                FSH.remove_FS_entry(entry.realpath)
                fcnt += 1

        #rename the dirs
        for dir_entry in reversed(dir_entries):
            if FSH.remove_FS_entry(dir_entry):
                dcnt += 1

        # print summary
        if not quiet:
            print('Renamed: {0} files, {1} folders'.format(fcnt, dcnt))




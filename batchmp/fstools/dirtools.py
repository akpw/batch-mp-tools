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
from batchmp.fstools.walker import DWalker
from batchmp.fstools.fsutils import FSH
from batchmp.fstools.builders.fsentry import FSEntry, FSEntryType, FSEntryParamsExt
# from profilehooks import profile


class DHandler:
    ''' FS Directory level utilities
    '''
    @staticmethod
#    @profile
    def print_dir(fs_entry_params, formatter = None, selected_files_description = None):
        """ Prints content of given directory
            Supports additional display name processing via formatter supplied by the caller
        """
        if not os.path.exists(fs_entry_params.src_dir):
            raise ValueError('Not a valid path')

        if formatter is None:
            formatter = lambda entry: entry.basename

        if selected_files_description is None:
            selected_files_description = 'file'

        # print the dir tree
        fcnt = dcnt = 0
        total_file_size = 0
        total_dir_size = 0

        for entry in DWalker.entries(fs_entry_params):
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
                if entry.type == FSEntryType.FILE:
                    fcnt += 1
                    if fs_entry_params.show_size:
                        fsize = os.path.getsize(entry.realpath)
                        size = ' {} '.format(FSH.fs_size(fsize))
                        total_file_size += fsize
                elif entry.type == FSEntryType.DIR and not entry.isEnclosingEntry:
                    dcnt += 1
                    if fs_entry_params.show_size:
                        dsize = FSH.dir_size(entry.realpath)
                        size = ' {} '.format(FSH.fs_size(dsize))
                        total_dir_size += dsize

                print('{0}{1}{2}'.format(entry.indent, size, formatted_output))

        # print summary
        print('{0} {1}{2}, {3} folder{4}'.format(fcnt,
                                                    selected_files_description, '' if fcnt == 1 else 's',
                                                    dcnt, '' if dcnt == 1 else 's'))
        if fs_entry_params.show_size:
            print('Total directories size: {}'.format(FSH.fs_size(total_dir_size)))
            if total_file_size > 0:
                print('Total selected files size: {}'.format(FSH.fs_size(total_file_size)))

        return fcnt, dcnt

    @staticmethod
    def dir_stats(fs_entry_params, 
                    include_size = False,
                    file_pass_filter = None, dir_pass_filter = None):
        """ Returns base stats for given directory
        """
        if not os.path.exists(fs_entry_params.src_dir):
            raise ValueError('Not a valid path')

        # count number of files, folders, and their total size
        fcnt = dcnt = total_size = 0
        for entry in DWalker.entries(fs_entry_params):

            if entry.type == FSEntryType.FILE:
                if file_pass_filter and (not file_pass_filter(entry.realpath)):
                    continue
                fcnt += 1
            elif entry.type == FSEntryType.DIR:
                if entry.isEnclosingEntry:
                    continue
                if dir_pass_filter and (not dir_pass_filter(entry.realpath)):
                    continue
                if FSH.level_from_root(fs_entry_params.src_dir, entry.realpath) > fs_entry_params.start_level:
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
    def visualise_changes(fs_entry_params, 
                            before_msg = 'Current source directory:',
                            after_msg = 'Targeted after processing:',                
                            preformatter = None, formatter = None, reset_formatters = None,
                            selected_files_description = None, fs_preprocess_entry_params = None):

        ''' Displays targeted changes and gets users' confirmation on futher processing
        '''
        if not fs_preprocess_entry_params: 
            fs_preprocess_entry_params = fs_entry_params

        if fs_preprocess_entry_params.display_current:
            print(before_msg)
            DHandler.print_dir(fs_preprocess_entry_params,
                                formatter = preformatter,
                                selected_files_description = selected_files_description)
            if reset_formatters:
                reset_formatters()
            print()

        print(after_msg)
        fcnt, dcnt = DHandler.print_dir(fs_entry_params,
                                            formatter = formatter,
                                            selected_files_description = selected_files_description)
        if fcnt == dcnt == 0:
            print ('Nothing to process')
            return False
        else:
            return DHandler.get_user_input()

    @staticmethod
    def flatten_folders(ff_entry_params, 
                        remove_folders = True, remove_non_empty_folders = False):
        ''' Flattens all folders below target level, moving the files up at the target level
        '''
        fs_preprocess_entry_params = FSEntryParamsExt()
        fs_preprocess_entry_params.copy_params(ff_entry_params)

        proceed = True if ff_entry_params.quiet else DHandler.visualise_changes(ff_entry_params, fs_preprocess_entry_params = fs_preprocess_entry_params)
        if proceed:
            # OK to go
            flattened_dirs_cnt = flattened_files_cnt = 0
            target_dir_path = ''
            for entry in DWalker.entries(ff_entry_params):
                if entry.type in (FSEntryType.DIR, FSEntryType.ROOT):
                    if FSH.level_from_root(ff_entry_params.src_dir, entry.realpath) == ff_entry_params.target_level:
                        target_dir_path = entry.realpath
                else:
                    # files                    
                    if target_dir_path and (FSH.level_from_root(ff_entry_params.src_dir, entry.realpath) - 1 > ff_entry_params.target_level):
                        target_fpath = os.path.join(target_dir_path, entry.basename)
                        if FSH.move_FS_entry(entry.realpath, target_fpath):
                            flattened_files_cnt += 1

            # remove excessive folders
            if ff_entry_params.remove_folders:
                flattened_dirs_cnt = FSH.remove_folders_below_target_level(ff_entry_params.src_dir,
                                                       target_level = ff_entry_params.target_level,
                                                       empty_only = not ff_entry_params.remove_non_empty_folders)
            # print summary
            if not ff_entry_params.quiet:
                print('Flattened: {0} files, {1} folders'.format(flattened_files_cnt, flattened_dirs_cnt))

        if not ff_entry_params.quiet:
            print('\nDone')

    @staticmethod
    def rename_entries(fs_entry_params,
                        formatter = None, check_unique = True):

        """ Renames directory entries via applying formatter function supplied by the caller
        """
        if not formatter:
            return

        fcnt = dcnt = 0
        DirEntry = namedtuple('DirEntry', ['orig_path', 'target_path'])
        dir_entries = []
        for entry in DWalker.entries(fs_entry_params):

            if entry.type == FSEntryType.ROOT:
                continue

            target_name = formatter(entry)
            if target_name == entry.basename:
                continue

            target_path = os.path.join(os.path.dirname(entry.realpath), target_name)

            if entry.type == FSEntryType.DIR:
                # for dirs, need to postpone
                dir_entries.append(DirEntry(entry.realpath, target_path))

            elif entry.type == FSEntryType.FILE:
                # for files, just rename
                if FSH.move_FS_entry(entry.realpath, target_path, check_unique = check_unique):
                    fcnt += 1

        #rename the dirs
        for dir_entry in reversed(dir_entries):
            if FSH.move_FS_entry(dir_entry.orig_path, dir_entry.target_path, check_unique = check_unique):
                dcnt += 1

        # print summary
        if not fs_entry_params.quiet:
            print('Renamed: {0} files, {1} folders'.format(fcnt, dcnt))

    @staticmethod
    def remove_entries(fs_entry_params,
                        formatter = None):

        """ Removes entries with formatter function supplied by the caller
        """
        if not formatter:
            return

        fcnt = dcnt = 0
        dir_entries = []
        for entry in DWalker.entries(fs_entry_params):

            if entry.type == FSEntryType.ROOT or entry.isEnclosingEntry:
                continue

            if formatter(entry) is None:
                continue

            if entry.type == FSEntryType.DIR:
                # for dirs, need to postpone
                dir_entries.append(entry.realpath)

            elif entry.type == FSEntryType.FILE:
                # for files, OK to remove now
                FSH.remove_FS_entry(entry.realpath)
                fcnt += 1

        #rename the dirs
        for dir_entry in reversed(dir_entries):
            FSH.remove_FS_entry(dir_entry)
            dcnt += 1

        # print summary
        if not fs_entry_params.quiet:
            print('Removed: {0} files, {1} folders'.format(fcnt, dcnt))




#!/usr/bin/env python
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


""" Batch renaming of files and directories
      . supports source directory / source file modes
      . visualises original / targeted folders structure before actual processing
      . supports recursion to specified end_level
      . supports flattening folders beyond specified end_level
      . allows for include / exclude patterns (Unix style)
      . allows global include/exclude of directories and folders
      . display sorting:
          .. by size/date, ascending/descending
      . action commands:
          .. print      Prints source directory
          .. flatten    Flatten all folders below target level, moving the files up
                            at the target level. By default, deletes all empty flattened folders
          .. index      Adds index to files and directories names
          .. add_date   Adds date to files and directories names
          .. add_text   Adds text to files and directories names
          .. remove     Removes n characters from files and directories names
          .. replace    RegExp-based replace in files and directories names
          .. capitalize Capitalizes words in files / directories names
          .. delete     Delete selected files and directories

    Usage: renamer [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
      Input source mode:
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Recursion mode:
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

      Filter files or folders:
        [-in, --include]            Include: Unix-style name patterns separated by ';'
        [-ex, --exclude]            Exclude: Unix-style name patterns separated by ';'
        [-fd, --filter-dirs]        Enable  Include/Exclude patterns on directories
        [-af, --all-files]          Disable Include/Exclude patterns on files

      Miscellaneous:
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands:
        {print, flatten, index, add_date, add_text, remove, replace, capitalize, delete}
        $ renamer {command} -h  #run this for detailed help on individual commands
"""
import sys
from argparse import ArgumentParser
from scripts.base.bmpbs import BMPBaseArgParser
from batchmp.ffmptools.ffutils import FFH, FFmpegNotInstalled
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.rename import Renamer


class RenameArgParser(BMPBaseArgParser):
    ''' Renamer commands parsing
    '''
    @classmethod
    def parse_commands(cls, parser):
        ''' parses Renamer commands
        '''
        # Commands
        subparsers = parser.add_subparsers(dest = 'sub_cmd', title = 'Renamer Commands')

        def add_include_mode_group(parser):
            include_mode_group = parser.add_argument_group('Include for processing')
            include_mode_group.add_argument("-id", "--include-dirs", dest = "include_dirs",
                help = "Include directories for processing",
                action = 'store_true')
            include_mode_group.add_argument("-ef", "--exclude-files", dest = "exclude_files",
                help = "Exclude files from processing",
                action = 'store_true')

        # Print
        print_parser = subparsers.add_parser('print', description = 'Print source directory')
        print_parser.add_argument('-sl', '--start-level', dest = 'start_level',
                help = 'Initial nested level for printing (0, i.e. root source directory by default)',
                type = int,
                default = 0)
        print_parser.add_argument('-ss', '--show-size', dest = 'show_size',
                help ='Show files size',
                action = 'store_true')

        # Flatten
        flatten_parser = subparsers.add_parser('flatten',
                description = 'Flatten all folders below target level, moving the files up the target level. \
                                                  By default, all empty flattened folders will be deleted.')
        flatten_parser.add_argument('-tl', '--target-level', dest = 'target_level',
                help = 'Target level below which all folders will be flattened',
                type = int,
                required = True)
        flatten_parser.add_argument('-df', '--discard-flattened', dest = 'discard_flattened',
                help = "What to do with flattened directories: \
                              'de' (default) will remove flattened directories if they are empty \
                              'le' will leave flattened directories (empty or not) \
                              'da' will discard flattened directories even if they are not empty",
                type=str,
                choices = ['de', 'le', 'da'],
                default = 'de')
        cls.add_arg_display_curent_state_mode(flatten_parser)

        # Add index
        add_index_parser = subparsers.add_parser('index', description = 'Adds index to files and directories names')
        add_index_parser.add_argument('-sf', '--start-from', dest = 'start_from',
                help = 'A number from which the indexing starts (1 by default)',
                type = int,
                default = 1)

        add_index_type_group = add_index_parser.add_mutually_exclusive_group()
        add_index_type_group.add_argument('-sq', '--sequential', dest = 'sequential',
                help = 'Index selected files sequentially. ' \
                       'If omitted, the files will instead be indexed within their respective directories (multi-level indexing)',
                action = 'store_true')
        add_index_type_group.add_argument('-bd', '--by-directory', dest = 'by_directory',
                help = 'Index selected files via adding their respective directory counter. ' \
                       'If omitted, the files will instead be indexed within their respective directories (multi-level indexing)',
                action = 'store_true')
        add_index_parser.add_argument('-as', '--as-suffix', dest = 'as_suffix',
                help = 'Add index at the end of file names',
                action = 'store_true')
        add_index_parser.add_argument('-js', '--join-string', dest = 'join_str',
                help = "Join string for appending indices (' ' by default)",
                type = str,
                default = ' ')
        add_index_parser.add_argument('-md', '--min-digits', dest = 'min_digits',
                help = 'Minimal number of digits for indexing (2 by default, and adding leading zeros as needed)',
                type = int,
                default = 2)
        add_include_mode_group(add_index_parser)
        cls.add_arg_display_curent_state_mode(add_index_parser)

        # Add Date
        add_date_parser = subparsers.add_parser('add_date', description = 'Adds date to files and directories names')
        add_date_parser.add_argument('-ap', '--as-prefix', dest = 'as_prefix',
                help = 'Add date as a prefix to file names',
                action = 'store_true')
        add_date_parser.add_argument('-js', '--join-string', dest = 'join_str',
                help = "Join string for appending dates ('_' by default)",
                type = str,
                default = '_')
        add_date_parser.add_argument('-fm', '--format', dest = 'format',
                help = 'Date format',
                type = str,
                default = '%Y-%m-%d')
        add_include_mode_group(add_date_parser)
        cls.add_arg_display_curent_state_mode(add_date_parser)

        # Add Text
        add_text_parser = subparsers.add_parser('add_text', description = 'Adds text to files and directories names')
        add_text_parser.add_argument('-ap', '--asprefix', dest = 'as_prefix',
                help = 'Add text as a prefix to file names',
                action = 'store_true')
        add_text_parser.add_argument('-js', '--join-string', dest = 'join_str',
                help = "Join string for appending text ('_' by default)",
                type = str,
                default = '_')
        add_text_parser.add_argument('-tx', '--text', dest = 'text',
                help = 'Text to add',
                type = str,
                required = True)
        add_include_mode_group(add_text_parser)
        cls.add_arg_display_curent_state_mode(add_text_parser)

        # Remove chars
        remove_chars_parser = subparsers.add_parser('remove', description = 'Removes n characters from files and directories names')
        remove_chars_parser.add_argument('-nc', '--num-chars', dest = 'num_chars',
                help = "Number of characters to remove",
                type = int,
                required = True)
        remove_chars_parser.add_argument('-ft', '--from-tail', dest = 'from_tail',
                help = 'Removes text from tail',
                action = 'store_true')
        add_include_mode_group(remove_chars_parser)
        cls.add_arg_display_curent_state_mode(remove_chars_parser)

        # Replace
        replace_parser = subparsers.add_parser('replace', description = 'RegExp-based replace in files and directories names')
        replace_parser.add_argument('-fs', '--find-string', dest = 'find_str',
                help = "Find pattern to look for",
                type = str,
                required=True)
        replace_parser.add_argument('-rs', '--replace-string', dest = 'replace_str',
                help = "Replace pattern to replace with.\
                        If not specified and there is a match from the find pattern, \
                        the entire string will be replaced with that match",
                type = str)
        replace_parser.add_argument('-ic', '--ignore-case', dest = 'ignore_case',
                help = 'Case insensitive',
                action = 'store_true')
        replace_parser.add_argument('-ie', '--include-extension', dest = 'include_extension',
                help = 'Include file extension',
                action = 'store_true')
        add_include_mode_group(replace_parser)
        cls.add_arg_display_curent_state_mode(replace_parser)

        # Capitalize
        capitalize_parser = subparsers.add_parser('capitalize', description = 'Capitalizes words in files / directories names')
        add_include_mode_group(capitalize_parser)
        cls.add_arg_display_curent_state_mode(capitalize_parser)

        # Delete
        delete_parser = subparsers.add_parser('delete', description = 'Delete selected files and directories')
        delete_parser.add_argument('-nm', '--non-media', dest = 'non_media_files_only',
                help = 'Delete all non-media files only',
                action = 'store_true')
        cls.add_arg_display_curent_state_mode(delete_parser)
        add_include_mode_group(delete_parser)

    @classmethod
    def default_command(cls, args, parser):
        super().default_command(args, parser)
        args['show_size'] = False

    @classmethod
    def check_args(cls, args, parser):
        ''' Validation of supplied Renamer CLI arguments
        '''
        super().check_args(args, parser)

        if args['sub_cmd'] == 'flatten':
            if args['file']:
                parser.error('This operation requires a source directory')
            if args['end_level'] < args['target_level']:
                print ('Target Level should be greater than or equal to the End Level Global Option\n'
                           '... Adjusting End Level to: {}'.format(args['target_level']))
                args['end_level'] = args['target_level']

        elif args['sub_cmd'] == 'delete':
            if args['non_media_files_only']:
                if not FFH.ffmpeg_installed():
                    print(FFmpegNotInstalled().default_message)


class RenameDispatcher:
    ''' Renamer CLI Commands Dispatcher
    '''
    @staticmethod
    def print_dir(args):
        DHandler.print_dir(src_dir = args['dir'],
                start_level = args['start_level'], end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                show_size = args['show_size'])

    @staticmethod
    def flatten(args):
            remove_folders = True if args['discard_flattened'] in ('de', 'da') else False
            remove_all_folders = True if args['discard_flattened'] == 'da' else False

            DHandler.flatten_folders(src_dir = args['dir'],
                end_level = args['end_level'],
                target_level = args['target_level'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                remove_folders = remove_folders, remove_non_empty_folders = remove_all_folders,
                display_current = args['display_current'], quiet = args['quiet'])

    @staticmethod
    def add_index(args):
        Renamer.add_index(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                as_prefix = not args['as_suffix'], join_str = args['join_str'],
                start_from = args['start_from'], min_digits = args['min_digits'],
                sequential = args['sequential'], by_directory = args['by_directory'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    @staticmethod
    def add_date(args):
        Renamer.add_date(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                as_prefix = args['as_prefix'], join_str = args['join_str'],
                format = args['format'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    @staticmethod
    def add_text(args):
        Renamer.add_text(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                text = args['text'],
                as_prefix = args['as_prefix'], join_str = args['join_str'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    @staticmethod
    def remove(args):
        Renamer.remove_n_characters(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                num_chars = args['num_chars'], from_head = not args['from_tail'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    @staticmethod
    def replace(args):
        Renamer.replace(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                find_str = args['find_str'],
                replace_str = args['replace_str'] if 'replace_str' in args else None,
                case_insensitive = args['ignore_case'],
                include_extension = args['include_extension'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    @staticmethod
    def capitalize(args):
        Renamer.capitalize(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    @staticmethod
    def delete(args):
        Renamer.delete(src_dir = args['dir'],
                non_media_files_only = args['non_media_files_only'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    @staticmethod
    def dispatch():
        ''' Dispatches Renamer commands
        '''
        args = RenameArgParser.parse_options(script_name = 'renamer',
                                             description = \
                        '''
                        Renamer is a multi-platform batch rename tool. In addition to common
                        operations such as regexp-based replace, adding text / dates, etc.
                        it also supports multi-level indexing across nested directories,
                        flattening folders, and cleaning up non-media files.
                        As default behavior, Renamer visualises targeted changes and ask
                        for confirmation before actually doing anything.
                        ''')

        if args['sub_cmd'] == 'print':
            RenameDispatcher.print_dir(args)
        elif args['sub_cmd'] == 'flatten':
            RenameDispatcher.flatten(args)
        elif args['sub_cmd'] == 'index':
            RenameDispatcher.add_index(args)
        elif args['sub_cmd'] == 'add_date':
            RenameDispatcher.add_date(args)
        elif args['sub_cmd'] == 'add_text':
            RenameDispatcher.add_text(args)
        elif args['sub_cmd'] == 'remove':
            RenameDispatcher.remove(args)
        elif args['sub_cmd'] == 'replace':
            RenameDispatcher.replace(args)
        elif args['sub_cmd'] == 'capitalize':
            RenameDispatcher.capitalize(args)
        elif args['sub_cmd'] == 'delete':
            RenameDispatcher.delete(args)

def main():
    ''' Renamer entry point
    '''
    RenameDispatcher.dispatch()

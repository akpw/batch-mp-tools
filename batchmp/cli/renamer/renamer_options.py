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
          .. index      Adds index to files and directories names
          .. add_date   Adds date to files and directories names
          .. add_text   Adds text to files and directories names
          .. remove     Removes n characters from files and directories names
          .. replace    RegExp-based replace in files and directories names,
                                        with support for expandable templates
          .. capitalize Capitalizes words in files / directories names
          .. flatten    Flatten all folders below target level, moving the files up
                            at the target level. By default, deletes all empty flattened folders
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
                                      (excludes hidden files by default)
        [-fd, --filter-dirs]        Enable  Include/Exclude patterns on directories
        [-af, --all-files]          Disable Include/Exclude patterns on files
                                      (shows hidden files excluded by default)
      Miscellaneous:
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands:
        {print, index, add_date, add_text, remove, replace, capitalize, flatten, delete, version, info}
        $ renamer {command} -h  #run this for detailed help on individual commands
"""
import sys
from batchmp.cli.base.bmp_options import BatchMPArgParser, BatchMPHelpFormatter, BatchMPBaseCommands


class RenamerCommands(BatchMPBaseCommands):
    INDEX = 'index'
    ADD_DATE = 'add_date'
    ADD_TEXT = 'add_text'
    REMOVE = 'remove'
    REPLACE = 'replace'
    CAPITALIZE = 'capitalize'
    FLATTEN = 'flatten'
    DELETE = 'delete'
    STATS = 'stats'

    @classmethod
    def commands_meta(cls):
        return ''.join(('{',
                        '{}, '.format(cls.PRINT),
                        '{}, '.format(cls.INDEX),
                        '{}, '.format(cls.ADD_DATE),
                        '{}, '.format(cls.ADD_TEXT),
                        '{}, '.format(cls.REMOVE),
                        '{}, '.format(cls.REPLACE),
                        '{}, '.format(cls.CAPITALIZE),
                        '{}, '.format(cls.FLATTEN),
                        '{}, '.format(cls.DELETE),
                        '{}, '.format(cls.STATS),                        
                        '{}, '.format(cls.INFO),
                        '{}'.format(cls.VERSION),
                        '}'))


class RenameArgParser(BatchMPArgParser):
    ''' Renamer commands parsing
    '''
    def __init__(self):
        self._script_name = 'Renamer'
        self._description = \
        '''
        Renamer is a multi-platform batch rename tool.
        In addition to common rename operations such as
        regexp-based replace, adding text / dates, etc.
        it also supports multi-level indexing across
        nested directories, flattening folders, and
        cleaning up non-media files.

        As default behavior, Renamer visualises targeted
        changes and ask for confirmation before actually
        changing anything.
        '''
    # Args Parsing
    def parse_commands(self, parser):
        ''' Renamer commands parsing
        '''
        # Commands
        subparsers = parser.add_subparsers(dest = 'sub_cmd',
                                                title = 'Renamer Commands',
                                                        metavar = RenamerCommands.commands_meta())
        self._add_version(subparsers)
        self._add_info(subparsers)

        def _add_include_mode_group(parser):
            include_mode_group = parser.add_argument_group('Include for processing')
            include_mode_group.add_argument("-id", "--include-dirs", dest = "include_dirs",
                help = "Include directories for processing",
                action = 'store_true')
            include_mode_group.add_argument("-ef", "--exclude-files", dest = "exclude_files",
                help = "Exclude files from processing",
                action = 'store_true')

        # Print
        print_parser = subparsers.add_parser(RenamerCommands.PRINT,
                                                description = 'Print source directory',
                                                formatter_class = BatchMPHelpFormatter)
        print_parser.add_argument('-sl', '--start-level', dest = 'start_level',
                help = 'Initial nested level for printing (0, i.e. root source directory by default)',
                type = int,
                default = 0)
        print_parser.add_argument('-ss', '--show-size', dest = 'show_size',
                help ='Show files size',
                action = 'store_true')

        # Stats
        stats_parser = subparsers.add_parser(RenamerCommands.STATS,
                                                description = 'Prints directory stats',
                                                formatter_class = BatchMPHelpFormatter)
        stats_parser.add_argument('-ss', '--show-size', dest = 'show_size',
                help ='Show files size',
                action = 'store_true')
        

        # Flatten
        flatten_parser = subparsers.add_parser(RenamerCommands.FLATTEN,
                description = 'Flatten all folders below target level, moving the files up the target level. \
                                                  By default, all empty flattened folders will be deleted.',
                formatter_class = BatchMPHelpFormatter)
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
        self._add_arg_display_curent_state_mode(flatten_parser)

        # Add index
        add_index_parser = subparsers.add_parser(RenamerCommands.INDEX,
                                                 description = 'Adds index to files and directories names',
                                                formatter_class = BatchMPHelpFormatter)
        add_index_parser.add_argument('-sf', '--start-from', dest = 'start_from',
                help = 'A number from which the indexing starts (1 by default)',
                type = int,
                default = 1)

        add_index_type_group = add_index_parser.add_mutually_exclusive_group()
        add_index_type_group.add_argument('-sq', '--sequential', dest = 'sequential',
                help = 'Index selected files sequentially across selected directores. ' \
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
        _add_include_mode_group(add_index_parser)
        self._add_arg_display_curent_state_mode(add_index_parser)

        # Add Date
        add_date_parser = subparsers.add_parser(RenamerCommands.ADD_DATE,
                                                description = 'Adds date to files and directories names',
                                                formatter_class = BatchMPHelpFormatter)
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
        _add_include_mode_group(add_date_parser)
        self._add_arg_display_curent_state_mode(add_date_parser)

        # Add Text
        add_text_parser = subparsers.add_parser(RenamerCommands.ADD_TEXT,
                                                description = 'Adds text to files and directories names',
                                                formatter_class = BatchMPHelpFormatter)
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
        _add_include_mode_group(add_text_parser)
        self._add_arg_display_curent_state_mode(add_text_parser)

        # Remove chars
        remove_chars_parser = subparsers.add_parser(RenamerCommands.REMOVE,
                                            description = 'Removes n characters from files and directories names',
                                            formatter_class = BatchMPHelpFormatter)
        remove_chars_parser.add_argument('-nc', '--num-chars', dest = 'num_chars',
                help = "Number of characters to remove",
                type = int,
                required = True)
        remove_chars_parser.add_argument('-ft', '--from-tail', dest = 'from_tail',
                help = 'Removes text from tail',
                action = 'store_true')
        _add_include_mode_group(remove_chars_parser)
        self._add_arg_display_curent_state_mode(remove_chars_parser)

        # Replace
        replace_parser = subparsers.add_parser(RenamerCommands.REPLACE,
                                            description = 'RegExp-based replace in files and directories names. ' \
                                                   'Supports expandable templates, such as ' \
                                                   '$dirname, $pardirname, $atime, $ctime, etc. ' \
                                                   'For media files, also support tag-based templates such as ' \
                                                   '$title, $album, $artist, $albumartist, $genre, $year, $track, etc.',
                                            formatter_class = BatchMPHelpFormatter)
        replace_parser.add_argument('-fs', '--find-string', dest = 'find_str',
                help = "Find pattern to look for",
                type = str,
                required=True)
        replace_parser.add_argument('-rs', '--replace-string', dest = 'replace_str',
                help = 'Replace pattern to replace with.\
                        If not specified and there is a match from the find pattern, \
                        the entire string will be replaced with that match. ' \
                        'Supports the following expandable templates: ' \
                                                   '$dirname, $pardirname, $adtime, $cdtime, $mdtime, ' \
                                                   '$atime, $ctime, $mtime, $adate, $cdate, $mdate. ' \
                                                   'For media files, also support tag-based templates such as ' \
                                                   '$title, $album, $artist, $albumartist, $genre, $year, $track, etc.',
                        type = str)
        replace_parser.add_argument('-ic', '--ignore-case', dest = 'ignore_case',
                help = 'Case insensitive',
                action = 'store_true')
        replace_parser.add_argument('-ie', '--include-extension', dest = 'include_extension',
                help = 'Include file extension',
                action = 'store_true')
        _add_include_mode_group(replace_parser)
        self._add_arg_display_curent_state_mode(replace_parser)

        # Capitalize
        capitalize_parser = subparsers.add_parser(RenamerCommands.CAPITALIZE,
                                                description = 'Capitalizes words in files / directories names',
                                                formatter_class = BatchMPHelpFormatter)
        _add_include_mode_group(capitalize_parser)
        self._add_arg_display_curent_state_mode(capitalize_parser)

        # Delete
        delete_parser = subparsers.add_parser(RenamerCommands.DELETE,
                                            description = 'Delete selected files and directories',
                                            formatter_class = BatchMPHelpFormatter)
        _add_include_mode_group(delete_parser)
        self._add_arg_display_curent_state_mode(delete_parser)


    # Args Checking
    def default_command(self, args, parser):
        args['sub_cmd'] = RenamerCommands.PRINT
        args['start_level'] = 0
        args['show_size'] = False

    def check_args(self, args, parser):
        ''' Validation of supplied Renamer CLI arguments
        '''
        super().check_args(args, parser)

        if args['sub_cmd'] == RenamerCommands.FLATTEN:
            if args['file']:
                parser.error('This operation requires a source directory')
            if args['end_level'] <= args['target_level']:
                #print ('Target Level should be greater than or equal to the End Level Global Option\n'
                #           '... Adjusting End Level to: {}'.format(args['target_level']))
                args['end_level'] = args['target_level']






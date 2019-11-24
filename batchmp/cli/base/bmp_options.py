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


""" Global options parsing:
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
                                      (excludes hidden files by default)
        [-ad, --all-dirs]           Prevent using Include/Exclude patterns on directories
        [-af, --all-files]          Prevent using Include/Exclude patterns on files
                                      (shows hidden files excluded by default)

        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing
"""

import os, sys, string
from argparse import ArgumentParser, HelpFormatter
from distutils.util import strtobool
from urllib.parse import urlparse
from batchmp.commons.utils import MiscHelpers
from batchmp.fstools.fsutils import FSH
from batchmp.fstools.builders.fsentry import FSEntry, FSEntryDefaults
from batchmp.ffmptools.ffutils import FFH, FFmpegNotInstalled


class BatchMPBaseCommands:
    VERSION = 'version'
    INFO = 'info'
    PRINT = 'print'

    @classmethod
    def commands_meta(cls):
        return ''.join(('{',
                        '{}, '.format(cls.INFO),
                        '{}'.format(cls.VERSION),
                        '}'))

class BatchMPArgParser:
    def __init__(self):
        self._script_name = 'BatchMP'
        self._description = \
    '''
    BatchMP provide management of media files,
    from base properties such as file names
    through tags / artwork metadata to
    advanced operations on the media content.

    BatchMP tools  consist of three main command-line utilities.
    For more information, run:
        $ renamer -h
        $ tagger -h
        $ bmfp -h
    '''

    @property
    def description(self):
        return self._description

    @property
    def script_name(self):
        return self._script_name

    # Args parsing
    def parse_options(self):
        ''' Common workflow for parsing options
        '''
        parser = ArgumentParser(prog = self._script_name, description = self._description,
                                                                formatter_class=BatchMPHelpFormatter)

        self.parse_global_options(parser)

        self.parse_commands(parser)

        args = vars(parser.parse_args())

        self.check_args(args, parser)

        return args

    def parse_global_options(self, parser):
        ''' Parses global options
        '''
        source_mode_group = parser.add_argument_group('Input source mode')
        source_mode_group.add_argument("-d", "--dir", dest = "dir",
                    type = lambda d: self._is_valid_dir_path(parser, d),
                    help = "Source directory (default is current directory)",
                    default = os.curdir)
        source_mode_group.add_argument("-f", "--file", dest = "file",
                    type = lambda f: self._is_valid_file_path(parser, f),
                    help = "File to process")

        recursive_mode_group = parser.add_argument_group('Recursion mode')
        recursive_mode_group.add_argument("-r", "--recursive", dest = "recursive",
                    help = "Recurse into nested folders",
                    action = 'store_true')
        recursive_mode_group.add_argument("-el", "--end-level", dest = "end_level",
                    help = "End level for recursion into nested folders",
                    type = int,
                    default = 0)

        include_mode_group = parser.add_argument_group('Filter files or folders')
        include_mode_group.add_argument("-in", "--include", dest = "include",
                    help = "Include: Unix-style name patterns separated by ';'",
                    type = str,
                    default =  FSEntryDefaults.DEFAULT_INCLUDE)
        include_mode_group.add_argument("-ex", "--exclude", dest = "exclude",
                    help = "Exclude: Unix-style name patterns separated by ';' (excludes hidden files by default)",
                    type = str,
                    default =  FSEntryDefaults.DEFAULT_EXCLUDE)
        include_mode_group.add_argument("-ad", "--all-dirs", dest = "all_dirs",
                    help = "Disable Include/Exclude patterns on directories",
                    action = 'store_true')
        include_mode_group.add_argument("-af", "--all-files", dest = "all_files",
                    help = "Disable Include/Exclude patterns on files (shows hidden files excluded by default)",
                    action = 'store_true')

        media_types_group = parser.add_argument_group('File media types')
        media_types_group.add_argument("-ft", "--file-type", dest = "file_type",
                    help = "File Media Type",
                    type = str,
                    choices = ['image', 'video', 'audio', 'media', 'nonmedia', 'playable', 'nonplayable', 'any'],
                    default =  FSEntryDefaults.DEFAULT_FILE_TYPE)
        media_types_group.add_argument("-ms", "--media-scan", dest = "media_scan",
                    help = "Scan for media types, instead of using file extensions (can take a long time)",
                    action = 'store_true')


        # Add Default Miscellaneous Group
        self._add_arg_misc_group(parser)

    def parse_commands(self, parser):
        ''' Specific commands parsing
        '''
        subparsers = parser.add_subparsers(dest = 'sub_cmd',
                                            title = 'BatchMP commands',
                                                metavar = BatchMPBaseCommands.commands_meta())
        self._add_version(subparsers)
        self._add_info(subparsers)

    # Args checking
    def check_cmd_args(self, args, parser,
                        show_help = False,
                        exit = False):
        if not args.get('sub_cmd'):
            if show_help:
                parser.print_help()
            if exit:
                sys.exit(1)

            # if not exiting, need to default
            self.default_command(args, parser)

    def default_command(self, args, parser):
        args['sub_cmd'] = BatchMPBaseCommands.INFO

    def check_args(self, args, parser):
        ''' Validation of supplied CLI arguments
        '''
        # check if there is a cmd to execute
        self.check_cmd_args(args, parser)

        # if input source is a file, need to adjust
        if args['file']:
            args['dir'] = os.path.dirname(args['file'])
            args['include'] = os.path.basename(args['file'])
            args['exclude'] = ''
            args['end_level'] = 0
            args['all_files'] = False
            args['all_dirs'] = False

        # check recursion
        if args['recursive'] and args['end_level'] == 0:
            args['end_level'] = sys.maxsize


        if args['media_scan']:
            if not FFH.ffmpeg_installed():
                print('Advanced media-related operations require FFmpeg')
                print(FFmpegNotInstalled().default_message)
                sys.exit(0)

        if args['sub_cmd'] == BatchMPBaseCommands.PRINT:
            if args['start_level'] != 0:
                if args['file']:
                    print ('Start Level parameter requires a source directory\n Ignoring requested Start Level...')
                    args['start_level'] = 0
                elif args['end_level'] < args['start_level']:
                    ''' print ('Start Level should be greater than or equal to the Recursion End Level Global Option\n'
                           '... Adjusting End Level to: {}'.format(args['start_level']))
                    '''
                    args['end_level'] = args['start_level']

    # Internal Helpers
    @staticmethod
    def _is_valid_dir_path(parser, path_arg):
        """ Checks if path_arg is a valid dir path
        """
        path_arg = FSH.full_path(path_arg)
        if not (os.path.exists(path_arg) and os.path.isdir(path_arg)):
            parser.error('"{}" does not seem to be an existing directory path'.format(path_arg))
        else:
            return path_arg

    @staticmethod
    def _is_valid_file_path(parser, path_arg):
        """ Checks if path_arg is a valid file path
        """
        path_arg = FSH.full_path(path_arg)
        if not (os.path.exists(path_arg) and os.path.isfile(path_arg)):
            parser.error('"{}" does not seem to be an existing file path'.format(path_arg))
        else:
            return path_arg

    @staticmethod
    def _is_boolean(parser, bool_arg):
        """ Checks if bool_arg can be interpreted as a boolean value
        """
        try:
            bool_arg = True if strtobool(bool_arg) else False
        except ValueError:
            parser.error('"{}": Please enter a boolean value'.format(bool_arg))
            return False

    @staticmethod
    def _is_valid_url(parser, url_arg):
        url_parts = urlparse(url_arg)

        def _parser_error():
            parser.error('"{}": Please enter a valid URL'.format(url_arg))

        if url_parts.scheme in (None, '') and url_parts.netloc in (None, ''):
            _parser_error()

        if url_parts.scheme == 'file':
            if url_parts.netloc == '~':
                fpath = '~{}'.format(url_parts.path)
            else:
                fpath = url_parts.path
            return BatchMPArgParser._is_valid_file_path(parser, fpath)

        if not set(url_parts.netloc).issubset(set(string.ascii_letters + string.digits + '-.')):
            _parser_error()

        if not url_parts.scheme in ['http', 'https', 'ftp', 'file']:
            _parser_error()

        return url_arg

    @staticmethod
    def _is_valid_url_or_file_path(parser, url_or_file_path_arg):
        url_parts = urlparse(url_or_file_path_arg)
        if url_parts.scheme in (None, '') and url_parts.netloc in (None, ''):
            return BatchMPArgParser._is_valid_file_path(parser, url_or_file_path_arg)
        else:
            return BatchMPArgParser._is_valid_url(parser, url_or_file_path_arg)

    @staticmethod
    def _is_timedelta(parser, td_arg):
        try:
            td = MiscHelpers.time_delta(td_arg)
        except ValueError:
            parser.error('"{}": Please enter a valid value, ' \
                         'in seconds or in the "hh:mm:ss[.xxx]" format'.format(td_arg))
        return  td

    # Processing mode for relevant commands
    @staticmethod
    def _add_arg_display_curent_state_mode(parser):
        parser.add_argument('-dc', '--display-current', dest = 'display_current',
                help ='Unless in quiet mode, display current (pre-processing) state in the confirmation propmt',
                action = 'store_true')

    @staticmethod
    def _add_arg_misc_group(parser):
        misc_group = parser.add_argument_group('Miscellaneous')
        misc_group.add_argument('-s', '--sort', dest = 'sort',
                    help = "Sorting for files ('na', i.e. by name ascending by default)",
                    type = str,
                    choices = ['na', 'nd', 'sa', 'sd'],
                    default = FSEntryDefaults.DEFAULT_SORT)
        misc_group.add_argument('-ni', '--nested_indent', dest = 'nested_indent',
                    help = "Indent for printing  nested directories",
                    type = str,
                    default = '  ')
        misc_group.add_argument("-q", "--quiet", dest = 'quiet',
                    help = "Disable visualising changes & displaying info messages during processing",
                    action = 'store_true')

    @staticmethod
    def _add_version(parser):
        ''' Adds the version command
        '''
        parser.add_parser(BatchMPBaseCommands.VERSION,
                                description = 'Displays BatchMP version info',
                                        formatter_class=BatchMPHelpFormatter)

    @staticmethod
    def _add_info(parser):
        ''' Adds the info command
        '''
        parser.add_parser(BatchMPBaseCommands.INFO,
                                description = 'Displays BatchMP info',
                                        formatter_class=BatchMPHelpFormatter)



class BatchMPHelpFormatter(HelpFormatter):
    ''' Custom ArgumentParser formatter
        Disables double metavar display, showing it only for long-named options
    '''
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            # change to
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    #parts.append('%s %s' % (option_string, args_string))
                    parts.append('%s' % option_string)
                parts[-1] += ' %s'%args_string
            return ', '.join(parts)

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

import os, sys, datetime
from argparse import ArgumentParser

""" Global options parsing for scripts:
        [-r, --recursive]           Recurse into nested folders
        [-el, --endlevel]           End level for recursion into nested folders
        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --alldirs]            Prevent using Include/Exclude patterns on directories
        [-af, --allfiles]           Prevent using Include/Exclude patterns on files
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-q, --quiet]               Do not visualise changes / show messages during processing
"""
class BMPBaseArgParser:
    @staticmethod
    def is_valid_dir_path(parser, path_arg):
        """ Checks if path_arg is a valid dir path
        """
        path_arg = os.path.realpath(os.path.expanduser(path_arg))
        if not (os.path.exists(path_arg) and os.path.isdir(path_arg)):
            parser.error('Please enter a valid source directory path'.format(path_arg))
        else:
            return path_arg

    @staticmethod
    def is_valid_file_path(parser, path_arg):
        """ Checks if path_arg is a valid file path
        """
        path_arg = os.path.realpath(os.path.expanduser(path_arg))
        if not (os.path.exists(path_arg) and os.path.isfile(path_arg)):
            parser.error('Please enter a valid file path'.format(path_arg))
        else:
            return path_arg

    @staticmethod
    def is_boolean(parser, bool_arg):
        """ Checks if bool_arg can be interpreted as a boolean value
        """
        if len(bool_arg) < 1:
            parser.error('Please enter a boolean value')
        bool_arg = bool_arg[0].lower()
        if bool_arg == 't' or bool_arg == 'y' or bool_arg == '1':
            return True
        elif bool_arg == 'f' or bool_arg == 'n' or bool_arg == '0':
            return False
        else:
            parser.error('Please enter a boolean value')

    @staticmethod
    def is_timedelta(parser, td_arg):
        hrs = mins = secs = None
        td = td_arg.split(':')
        time_parts = range(len(td))
        for i in time_parts:
            if secs is None:
                secs = float(td.pop(-1))
            elif mins is None:
                mins = int(td.pop(-1))
            elif hrs is None:
                hrs = int(td.pop(-1))
            else:
                break
        return  datetime.timedelta(hours = hrs if hrs else 0,
                                      minutes = mins if mins else 0,
                                      seconds = secs if secs else 0)


    @staticmethod
    def parse_global_options(parser):
        # Global Options
        source_mode_group = parser.add_argument_group('Input source mode')
        source_mode_group.add_argument("-d", "--dir", dest = "dir",
                    type = lambda d: BMPBaseArgParser.is_valid_dir_path(parser, d),
                    help = "Source directory (default is current directory)",
                    default = os.curdir)
        source_mode_group.add_argument("-f", "--file", dest = "file",
                    type = lambda f: BMPBaseArgParser.is_valid_file_path(parser, f),
                    help = "File to process")

        recursive_mode_group = parser.add_argument_group('Recursion mode')
        recursive_mode_group.add_argument("-r", "--recursive", dest = "recursive",
                    help = "Recurse into nested folders",
                    action = 'store_true')
        recursive_mode_group.add_argument("-el", "--endlevel", dest = "end_level",
                    help = "End level for recursion into nested folders",
                    type = int,
                    default = 0)

        include_mode_group = parser.add_argument_group('Filter files or folders')
        include_mode_group.add_argument("-in", "--include",
                    help = "Include names pattern",
                    type = str,
                    default = '*')
        include_mode_group.add_argument("-ex", "--exclude",
                    help = "Exclude names pattern",
                    type = str,
                    default = '')
        include_mode_group.add_argument("-fd", "--alldirs", dest = "all_dirs",
                    help = "Disable Include/Exclude patterns on directories",
                    action = 'store_true')
        include_mode_group.add_argument("-af", "--allfiles", dest = "all_files",
                    help = "Disable Include/Exclude patterns on files",
                    action = 'store_true')

        misc_group = parser.add_argument_group('Miscellaneous')
        misc_group.add_argument('-s', '--sort', dest = 'sort',
                    help = "Sorting for files ('na', i.e. by name ascending by default)",
                    type=str,
                    choices = ['na', 'nd', 'sa', 'sd'],
                    default = 'na')
        misc_group.add_argument("-q", "--quiet", dest = 'quiet',
                    help = "Disable visualising changes & displaying info messages during processing",
                    action = 'store_true')

    @staticmethod
    def parse_commands(parser):
        pass

    @staticmethod
    def check_args(args, parser):
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

    @classmethod
    def parse_options(cls, script_name = 'batchmp tools', description = 'Global Options'):
        parser = ArgumentParser(prog = script_name, description = description)

        cls.parse_global_options(parser)

        cls.parse_commands(parser)

        args = vars(parser.parse_args())

        cls.check_args(args, parser)

        return args

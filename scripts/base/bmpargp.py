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

import os
from argparse import ArgumentParser

""" Global options parsing for scripts:
      . source dir / file
      . recursion to specified end_level
      . directory slicing, from start_level to end_level
      . include / exclude names patterns (Unix style)
      . enable or disable include / exclude for directories / folders
      . display sorting:
        .. by size/date, ascending/descending
"""
class BMPArgParser:
    @staticmethod
    def is_valid_dir_path(parser, path_arg):
        """ Checks if path_arg is a valid dir path
        """
        path_arg = os.path.realpath(path_arg)
        if not (os.path.exists(path_arg) and os.path.isdir(path_arg)):
            parser.error('Please enter a valid source directory path'.format(path_arg))
        else:
            return path_arg

    @staticmethod
    def is_valid_file_path(parser, path_arg):
        """ Checks if path_arg is a valid file path
        """
        path_arg = os.path.realpath(path_arg)
        if not (os.path.exists(path_arg) and os.path.isfile(path_arg)):
            parser.error('Please enter a valid file path'.format(path_arg))
        else:
            return path_arg

    @staticmethod
    def parse_global_options(parser):
        # Global Options
        parser.add_argument("-d", "--dir", dest = "dir",
                    type = lambda d: BMPArgParser.is_valid_dir_path(parser, d),
                    help = "Source directory (default is current directory)",
                    default = os.curdir)
        parser.add_argument("-f", "--file", dest = "file",
                    type = lambda f: BMPArgParser.is_valid_file_path(parser, f),
                    help = "File to process")
        parser.add_argument("-el", "--endlevel", dest = "end_level",
                    help = "End level for recursion into nested folders",
                    type = int,
                    default = 1)
        parser.add_argument("-in", "--include",
                    help = "Include names pattern",
                    type = str,
                    default = '*')
        parser.add_argument("-ex", "--exclude",
                    help = "Exclude names pattern",
                    type = str,
                    default = '')
        parser.add_argument("-fd", "--filterdirs", dest = "filter_dirs",
                    help = "Do not apply Include/Exclude patterns on directories",
                    action = 'store_true')
        parser.add_argument("-ff", "--filterfiles", dest = "filter_files",
                    help = "Do not apply Include/Exclude patterns on files",
                    action = 'store_true')
        parser.add_argument('-s', '--sort', dest = 'sort',
                    help = "Sorting for files ('na', i.e. by name ascending by default)",
                    type=str,
                    choices = ['na', 'nd', 'sa', 'sd'],
                    default = 'na')
        parser.add_argument("-q", "--quiet", dest = 'quiet',
                    help = "Do not visualise / show messages during processing",
                    action = 'store_true')

    @staticmethod
    def parse_commands(parser):
        pass

    @staticmethod
    def check_args(args):
        # if input source is a file, need to adjust
        if args['file']:
            args['dir'] = os.path.dirname(args['file'])
            args['include'] = os.path.basename(args['file'])
            args['exclude'] = ''
            args['end_level'] = 0
            args['filter_files'] = False
            args['filter_dirs'] = False

    @classmethod
    def parse_options(cls, script_name = 'batchmp tools', description = 'Global Options'):
        parser = ArgumentParser(prog = script_name, description = description)

        cls.parse_global_options(parser)

        cls.parse_commands(parser)

        args = vars(parser.parse_args())

        cls.check_args(args)

        return args



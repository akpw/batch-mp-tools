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
from batchmp.fstools.dirtools import DHandler

""" Batch renaming of files and directories
      . visualises original / targeted folders structure before actual rename action
      . supports recursion to specified end_level
      . supports flattening folders beyond end_level
      . can print directory from given a start_level to specified end_level
      . current rename actions:
          .. regexp-based replace
          .. add index
          .. add date
          .. add text
          .. remove n characters
      . allows for include / exclude patterns (Unix style)
      . allows global include/exclude of directories and folders
      . display sorting:
          .. by size/date, ascending/descending

    Usage: renamer -d DIR [GLobal Options] {Commands}

      Global Options:
          [-e END_LEVEL] [-i INCLUDE] [-e EXCLUDE]
          [-fd FILTER_DIRS] [-ff FILTER_FILES]
          [-id INCLUDE_DIRS] [-if INCLUDE_FILES]
          [-s SORT]
          [-q QUIET]
        Unless specified, uses the following defaults:
          . END_LEVEL:      0 (source directory level only, i.e. no recursion)
          . INCLUDE:        '*'
          . EXCLUDE:        ''
          . FILTER_DIRS:    True
          . FILTER_FILES:   True
          . INCLUDE_DIRS:   False
          . INCLUDE_FILES:  True
          . SORT:           By name, ascending
          . QUIET:          False

      Commands
"""

def is_valid_path(parser, path_arg):
    """ Checks if path_arg is a valid dir path
    """
    path_arg = os.path.realpath(path_arg)
    if not (os.path.exists(path_arg) and os.path.isdir(path_arg)):
        parser.error('Please enter a valid source directory'.format(path_arg))
    else:
        return path_arg

def parse_options():
  parser = ArgumentParser(prog = 'renamer')

  # Global Options
  parser.add_argument("-d", "--dir", dest = "dir",
              required=True,
              type = lambda d: is_valid_path(parser, d),
              help = "Source directory")
  parser.add_argument("-e", "--endlevel", dest = "end_level",
              help = "End level for recursion",
              type = int,
              default = 0)
  parser.add_argument("-in", "--include",
              help = "Include Pattern",
              type = str,
              default = '*')
  parser.add_argument("-ex", "--exclude",
              help = "Exclude Pattern",
              type = str,
              default = '')
  parser.add_argument("-fd", "--filterdirs", dest = "filter_dirs",
              help = "Use Include/Exclude patterns on directoris",
              action = 'store_true',
              default = True)
  parser.add_argument("-ff", "--filterfiles", dest = "filter_files",
              help = "Use Include/Exclude patterns on files",
              action = 'store_true',
              default = True)
  parser.add_argument("-id", "--includedirs", dest = "include_dirs",
              help = "Include directories for processing",
              action = 'store_true',
              default = False)
  parser.add_argument("-if", "--includefiles", dest = "include_files",
              help = "Include files for processing",
              action = 'store_true',
              default = True)
  parser.add_argument('-s', '--sort', nargs = '*', dest = 'sort',
              help = 'Sorting for files / folders',
              choices = ['sa', 'sd', 'da', 'dd'],
              default = 'sa')
  parser.add_argument("-q", "--quiet", dest = 'quiet',
              help = "Do not visualise / show messages during processing",
              action = 'store_true',
              default = False)

  # Commands
  subparsers = parser.add_subparsers(help='Renamer commands', dest='sub_cmd')

  # Print
  print_parser = subparsers.add_parser('print', help = 'Print source directory')
  print_parser.add_argument('-sl', '--startlevel', dest='start_level',
                  help='Start (sub)level for printing',
                  type=int,
                  default = 0)
  print_parser.add_argument('-ss', '--showsize', dest='show_size',
                  help='Show files size',
                  action = 'store_true',
                  default = False)

  # Flatten
  flatten_parser = subparsers.add_parser('flatten', help='Flatten folders below target level, \
                                                          moving their files at the target level')
  flatten_parser.add_argument('-tl', '--targetlevel', dest='target_level',
                  help='Target level below which all folders will be flattened',
                  type=int,
                  default = sys.maxsize)
  flatten_parser.add_argument('-rm', '--removeemptydirs', dest='remove_empty',
                  help='Remove flattened dirs, if empty',
                  action = 'store_true',
                  default = True)
  # Add index

  return vars(parser.parse_args())

def print_dir(args):
  DHandler.print_dir(src_dir = args['dir'],
                    start_level = args['start_level'], end_level = args['end_level'],
                    include = args['include'], exclude = args['exclude'], sort = args['sort'],
                    filter_dirs = args['filter_dirs'], filter_files = args['filter_files'],
                    flatten = False, ensure_uniq = False,
                    show_size = args['show_size'], formatter = None)

def flatten(args):
  DHandler.flatten_folders(src_dir = args['dir'],
                    target_level = args['target_level'],
                    include = args['include'], exclude = args['exclude'],
                    filter_dirs = True, filter_files = True,
                    remove_empty_folders = args['remove_empty'], quiet = args['quiet'])

def main():
  args = parse_options()
  print(args)

  if not args['sub_cmd']:
    args['sub_cmd'] = 'print'
    args['start_level'] = 0
    args['show_size'] = False

  if args['sub_cmd'] == 'print':
    print_dir(args)
  elif args['sub_cmd'] == 'flatten':
    flatten(args)


if __name__ == '__main__':
    main()


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
from batchmp.fstools.rename import Renamer

""" Batch renaming of files and directories
      . visualises original / targeted folders structure before actual rename action
      . supports recursion to specified end_level
      . supports flattening folders beyond end_level
      . can print directory from given a start_level to specified end_level
      . allows for include / exclude patterns (Unix style)
      . allows global include/exclude of directories and folders
      . rename actions:
          .. regexp-based replace
          .. add index
          .. add date
          .. add text
          .. remove n characters
      . display sorting:
          .. by size/date, ascending/descending

    Usage: renamer -d DIR [GLobal Options] {Commands}[Commands Options]
      Global Options (renamer -h for additional help)
        [-e END_LEVEL]                        End level for recursion into nested folders
        [-i INCLUDE] [-e EXCLUDE]             Include names pattern
        [-fd FILTER_DIRS] [-ff FILTER_FILES]  Use Include/Exclude patterns on dirs / files
        [-s SORT]                             Sorting for files / folders
        [-q QUIET]                            Do not visualise / show messages during processing
      renamer -h for additional help on global options

      Commands (renamer {command} -h for additional help)
      {print, flatten, index, date, text, remove,replace}
        print     Print source directory
        flatten   Flatten all folders below target level, moving the files
                                        up the target level. By default, all empty
                                        flattened folders will be deleted
        index     Add index to files and directories
        date      Add date to files and directories
        text      Add text to files and directories
        remove    Remove n characters from files and directories
        replace   RegExp-based replace in files and directories

      renamer Command -h for additional help
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
  parser = ArgumentParser(prog = 'renamer', description = 'Global Options')

  # Global Options
  parser.add_argument("-d", "--dir", dest = "dir",
              required = True,
              type = lambda d: is_valid_path(parser, d),
              help = "Source directory")
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

  # Commands
  subparsers = parser.add_subparsers(help = 'Renamer commands', dest='sub_cmd', title = 'Renamer Commands')

  # Print
  print_parser = subparsers.add_parser('print', help = 'Print source directory')
  print_parser.add_argument('-sl', '--startlevel', dest='start_level',
                  help = 'Initial nested level for printing (0, i.e. root source directory by default)',
                  type = int,
                  default = 0)
  print_parser.add_argument('-ss', '--showsize', dest='show_size',
                  help ='Show files size',
                  action = 'store_true')

  # Flatten
  flatten_parser = subparsers.add_parser('flatten',
                  help = 'Flatten all folders below target level, moving the files up the target level. \
                                                    By default, all empty flattened folders will be deleted.')
  flatten_parser.add_argument('-tl', '--targetlevel', dest='target_level',
                  help = 'Target level below which all folders will be flattened (a reasonably large number by default :)',
                  type = int,
                  default = sys.maxsize)
  flatten_parser.add_argument('-df', '--discardflattened', dest = 'discard_flattened',
              help = "What to do with flattened directories \
                            'de' (default) will remove flattened directories if they are empty \
                            'le' will leave flattened directories (empty or not) \
                            'da' will discard flattened directories even if they are not empty",
              type=str,
              choices = ['de', 'le', 'da'],
              default = 'na')

  # Add index
  add_index_parser = subparsers.add_parser('index', help = 'Adds index to files and directories')
  add_index_parser.add_argument('-ap', '--asprefix', dest='as_prefix',
                  help = 'Add index as prefix to names',
                  action = 'store_true')
  add_index_parser.add_argument('-js', '--joinstring', dest='join_str',
                  help = "Join string for appending indices ('_' by default)",
                  type = str,
                  default = '_')
  add_index_parser.add_argument('-sf', '--startfrom', dest='start_from',
                  help = 'A number from which the indexing starts (1 by default)',
                  type = int,
                  default = 1)
  add_index_parser.add_argument('-md', '--mindigits', dest='min_digits',
                  help = 'Minimal number of digits for indexing (2 by default, adding leading zeros as needed)',
                  type = int,
                  default = 2)
  add_index_parser.add_argument("-id", "--includedirs", dest = "include_dirs",
                  help = "Include directories for rename processing",
                  action = 'store_true')
  add_index_parser.add_argument("-ef", "--excludefiles", dest = "exclude_files",
                  help = "Exclude files from rename processing",
                  action = 'store_true')

  # Add Date
  add_date_parser = subparsers.add_parser('date', help = 'Adds date to files and directories')
  add_date_parser.add_argument('-ap', '--asprefix', dest='as_prefix',
                  help = 'Add date as prefix to names',
                  action = 'store_true')
  add_date_parser.add_argument('-js', '--joinstring', dest='join_str',
                  help = "Join string for appending dates ('_' by default)",
                  type = str,
                  default = '_')
  add_date_parser.add_argument('-fm', '--format', dest='format',
                  help = 'Date format',
                  type = str,
                  default = '%Y-%m-%d')
  add_date_parser.add_argument("-id", "--includedirs", dest = "include_dirs",
                  help = "Include directories for rename processing",
                  action = 'store_true')
  add_date_parser.add_argument("-ef", "--excludefiles", dest = "exclude_files",
                  help = "Exclude files from rename processing",
                  action = 'store_true')

  # Add Text
  add_text_parser = subparsers.add_parser('text', help = 'Adds text to files and directories')
  add_text_parser.add_argument('-ap', '--asprefix', dest='as_prefix',
                  help = 'Add text as prefix to names',
                  action = 'store_true')
  add_text_parser.add_argument('-js', '--joinstring', dest='join_str',
                  help = "Join string for appending text ('_' by default)",
                  type = str,
                  default = '_')
  add_text_parser.add_argument('-tx', '--text', dest='text',
                  help = 'Text to add',
                  type = str,
                  default = '')
  add_text_parser.add_argument("-id", "--includedirs", dest = "include_dirs",
                  help = "Include directories for rename processing",
                  action = 'store_true')
  add_text_parser.add_argument("-ef", "--excludefiles", dest = "exclude_files",
                  help = "Exclude files from rename processing",
                  action = 'store_true')

  # Remove chars
  remove_chars_parser = subparsers.add_parser('remove', help = 'Removes n characters from files and directories')
  remove_chars_parser.add_argument('-nc', '--numchars', dest='num_chars',
                  help = "Number of characters to remove (0 by default)",
                  type = int,
                  default = 0)
  remove_chars_parser.add_argument('-ft', '--fromtail', dest='from_tail',
                  help = 'Removes text from tail',
                  action = 'store_true')
  remove_chars_parser.add_argument("-id", "--includedirs", dest = "include_dirs",
                  help = "Include directories for rename processing",
                  action = 'store_true')
  remove_chars_parser.add_argument("-ef", "--excludefiles", dest = "exclude_files",
                  help = "Exclude files from rename processing",
                  action = 'store_true')

  # Replace
  add_text_parser = subparsers.add_parser('replace', help = 'RegExp-based replace in files and directories')
  add_text_parser.add_argument('-fs', '--findstring', dest='find_str',
                  help = "Find pattern to look for",
                  type = str,
                  required=True)
  add_text_parser.add_argument('-rs', '--replacestring', dest='replace_str',
                  help = "Replace pattern to replace with.\
                          If not specified and there is a match from the find pattern, \
                          the entire string will be replaced with that match",
                  type = str)
  add_text_parser.add_argument('-ic', '--ignorecase', dest='ignore_case',
                  help = 'Case insensitive',
                  action = 'store_true')
  add_text_parser.add_argument("-id", "--includedirs", dest = "include_dirs",
                  help = "Include directories for rename processing",
                  action = 'store_true')
  add_text_parser.add_argument("-ef", "--excludefiles", dest = "exclude_files",
                  help = "Exclude files from rename processing",
                  action = 'store_true')

  return vars(parser.parse_args())

# Worker functions
def print_dir(args):
  DHandler.print_dir(src_dir = args['dir'],
                    start_level = args['start_level'], end_level = args['end_level'],
                    include = args['include'], exclude = args['exclude'], sort = args['sort'],
                    filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                    flatten = False, ensure_uniq = False,
                    show_size = args['show_size'], formatter = None)

def flatten(args):
  end_level = args['end_level']
  target_level = args['target_level']
  if end_level < target_level:
    raise ValueError('Target Level for flattening should be greater than or equal to End Level')
  else:
    remove_folders = True if args['discard_flattened'] in ('de', 'da') else False
    remove_all_folders = True if args['discard_flattened'] == 'da' else False

    DHandler.flatten_folders(src_dir = args['dir'],
                    end_level = end_level,
                    target_level = target_level,
                    include = args['include'], exclude = args['exclude'],
                    filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                    remove_folders = remove_folders, remove_non_empty_folders = remove_all_folders,
                    quiet = args['quiet'])

def add_index(args):
  Renamer.add_index(src_dir = args['dir'], sort = args['sort'],
                    as_prefix = args['as_prefix'], join_str = args['join_str'],
                    start_from = args['start_from'], min_digits = args['min_digits'],
                    end_level = args['end_level'],
                    include = args['include'], exclude = args['exclude'],
                    filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                    include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                    quiet = args['quiet'])

def add_date(args):
  Renamer.add_date(src_dir = args['dir'], sort = args['sort'],
                    as_prefix = args['as_prefix'], join_str = args['join_str'],
                    format = args['format'],
                    end_level = args['end_level'],
                    include = args['include'], exclude = args['exclude'],
                    filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                    include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                    quiet = args['quiet'])

def add_text(args):
  Renamer.add_text(src_dir = args['dir'], sort = args['sort'],
                    text = args['text'],
                    as_prefix = args['as_prefix'], join_str = args['join_str'],
                    end_level = args['end_level'],
                    include = args['include'], exclude = args['exclude'],
                    filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                    include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                    quiet = args['quiet'])

def remove(args):
  Renamer.remove_n_characters(src_dir = args['dir'], sort = args['sort'],
                    num_chars = args['num_chars'], from_head = not args['from_tail'],
                    end_level = args['end_level'],
                    include = args['include'], exclude = args['exclude'],
                    filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                    include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                    quiet = args['quiet'])

def replace(args):
  Renamer.replace(src_dir = args['dir'], sort = args['sort'],
                    find_str = args['find_str'],
                    replace_str = args['replace_str'] if 'replace_str' in args else None,
                    case_insensitive = args['ignore_case'],
                    end_level = args['end_level'],
                    include = args['include'], exclude = args['exclude'],
                    filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                    include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                    quiet = args['quiet'])

def main():
  args = parse_options()
  if not args['sub_cmd']:
    args['sub_cmd'] = 'print'
    args['start_level'] = 0
    args['show_size'] = False

  if args['sub_cmd'] == 'print':
    print_dir(args)
  elif args['sub_cmd'] == 'flatten':
    flatten(args)
  elif args['sub_cmd'] == 'index':
    add_index(args)
  elif args['sub_cmd'] == 'date':
    add_date(args)
  elif args['sub_cmd'] == 'text':
    add_text(args)
  elif args['sub_cmd'] == 'remove':
    remove(args)
  elif args['sub_cmd'] == 'replace':
    replace(args)

if __name__ == '__main__':
    main()


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
from batchmp.tags.tagtools import THandler
from batchmp.tags.handlers import EmptyTagHandler
from batchmp.fstools.dirtools import DHandler
from functools import partial


""" Batch management of media files metadata
      . visualises original / targeted files metadata structure
      . action commands:
          .. print metadata info
          .. set metadata tags
          .. regexp-based replace in metadata
          .. index tracks
          .. extracts artwork
          .. add / remove title characters

    Usage: tagger {-d DIR} [GLobal Options] {Commands}[Commands Options]
      Global Options (renamer -h for additional help)
        [-e END_LEVEL]                        End level for recursion into nested folders
        [-i INCLUDE] [-e EXCLUDE]             Include names pattern
        [-fd FILTER_DIRS] [-ff FILTER_FILES]  Use Include/Exclude patterns on dirs / files
        [-s SORT]                             Sorting for files / folders
        [-q QUIET]                            Do not visualise / show messages during processing
      renamer -h for additional help on global options

      Commands (renamer {command} -h for additional help)
      {print, set}
        print     Print media directory
        set       Set tags in media files

      renamer Command -h for additional help
"""

def is_valid_dir_path(parser, dpath_arg):
    """ Checks if path_arg is a valid dir path
    """
    dpath_arg = os.path.realpath(dpath_arg)
    if not (os.path.exists(dpath_arg) and os.path.isdir(dpath_arg)):
        parser.error('Please enter a valid source directory path'.format(dpath_arg))
    else:
        return dpath_arg

def is_valid_file_path(parser, fpath_arg):
    """ Checks if path_arg is a valid dir path
    """
    fpath_arg = os.path.realpath(fpath_arg)
    if not (os.path.exists(fpath_arg) and os.path.isfile(fpath_arg)):
        parser.error('Please enter a valid file path'.format(fpath_arg))
    else:
        return fpath_arg

def parse_options():
  parser = ArgumentParser(prog = 'tagger', description = 'Global Options')

  # Global Options
  parser.add_argument("-d", "--dir", dest = "dir",
              type = lambda d: is_valid_dir_path(parser, d),
              help = "Source directory (default is current directory)",
              default = os.curdir)
  parser.add_argument("-el", "--endlevel", dest = "end_level",
              help = "End level for recursion into nested folders",
              type = int,
              default = 0)
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
  subparsers = parser.add_subparsers(help = 'Tagger commands', dest='sub_cmd', title = 'Tagger Commands')

  # Print
  print_parser = subparsers.add_parser('print', help = 'Print source directory')
  print_parser.add_argument('-sl', '--startlevel', dest='start_level',
                  help = 'Initial nested level for printing (0, i.e. root source directory by default)',
                  type = int,
                  default = 0)
  print_parser.add_argument('-ss', '--showsize', dest='show_size',
                  help ='Shows files size',
                  action = 'store_true')
  print_parser.add_argument('-st', '--showstats', dest='show_stats',
                  help ='Shows medial file statistics',
                  action = 'store_true')

  # Set Tags
  set_tags_parser = subparsers.add_parser('set', help = 'Sets specified tags in media files')
  set_tags_parser.add_argument('-ti', '--title', dest='title',
                  help = "Sets the title tag",
                  type = str)
  set_tags_parser.add_argument('-al', '--album', dest='album',
                  help = "Sets the album tag",
                  type = str)
  set_tags_parser.add_argument('-ar', '--artist', dest='artist',
                  help = "Sets the artist tag",
                  type = str)
  set_tags_parser.add_argument('-aa', '--albumArtist', dest='albumartist',
                  help = "Sets the album artist tag",
                  type = str)
  set_tags_parser.add_argument('-g', '--genre', dest='genre',
                  help = "Sets the genre tag",
                  type = str)
  set_tags_parser.add_argument('-c', '--composer', dest='composer',
                  help = "Sets the composer tag",
                  type = str)
  set_tags_parser.add_argument('-tr', '--track', dest='track',
                  help = "Sets the track tag",
                  type = str)
  set_tags_parser.add_argument('-tt', '--tracktotal', dest='tracktotal',
                  help = "Sets the tracktotal tag",
                  type = str)
  set_tags_parser.add_argument('-d', '--disc', dest='disc',
                  help = "Sets the disc tag",
                  type = str)
  set_tags_parser.add_argument('-dt', '--disctotal', dest='disctotal',
                  help = "Sets the disctotal tag",
                  type = str)
  set_tags_parser.add_argument('-y', '--year', dest='year',
                  help = "Sets the year tag",
                  type = str)
  set_tags_parser.add_argument('-at', '--art', dest='art',
                  help = "Sets artwork (/path to PNG or JPEG )",
                  type = lambda f: is_valid_file_path(parser, f))


  return vars(parser.parse_args())

# Worker functions
def print_dir(args):
  THandler().print_dir(src_dir = args['dir'],
                        sort = args['sort'],
                        start_level = args['start_level'], end_level = args['end_level'],
                        include = args['include'], exclude = args['exclude'],
                        filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                        flatten = False, ensure_uniq = False,
                        show_size = args['show_size'], show_stats = args['show_stats'], formatter = None)

def set_tags(args):
  tag_holder = EmptyTagHandler()
  tag_holder.title = args['title']
  tag_holder.album = args['album']
  tag_holder.artist = args['artist']
  tag_holder.albumartist = args['albumartist']
  tag_holder.genre = args['genre']
  tag_holder.composer = args['composer']
  tag_holder.track = args['track']
  tag_holder.tracktotal = args['tracktotal']
  tag_holder.disc = args['disc']
  tag_holder.disctotal = args['disctotal']
  tag_holder.year = args['year']

  art, art_path = None, args['art']
  if art_path:
    with open(art_path, 'rb') as f:
      art = f.read()
  if art:
    tag_holder.art = art

  # visualise changes to tags and proceed if confirmed
  tag_handler = THandler()
  preformatter = partial(tag_handler.tag_formatter, show_stats = False)
  formatter = partial(tag_handler.tag_formatter, tag_holder = tag_holder, show_stats = False)
  proceed = True if args['quiet'] else DHandler.visualise_changes(src_dir = args['dir'],
                        sort = args['sort'],
                        orig_end_level = args['end_level'], target_end_level = args['end_level'],
                        include = args['include'], exclude = args['exclude'],
                        filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                        preformatter = preformatter,
                        formatter = formatter)

  if proceed:
    tag_handler.set_tags(args['dir'],
                            start_level = 0, end_level = args['end_level'],
                            include = args['include'], exclude = args['exclude'],
                            filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                            tag_holder = tag_holder, quiet = args['quiet'])


def main():
  args = parse_options()
  if not args['sub_cmd']:
    args['sub_cmd'] = 'print'
    args['start_level'] = 0
    args['show_size'] = False
    args['show_stats'] = False

  if args['sub_cmd'] == 'print':
    print_dir(args)
  elif args['sub_cmd'] == 'set':
    set_tags(args)

if __name__ == '__main__':
    main()


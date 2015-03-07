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
from scripts.base.bmpbargp import BMPBaseArgParser
from batchmp.tags.processors.basetp import BaseTagProcessor
from batchmp.tags.handlers.tagsholder import TagHolder
from batchmp.tags.output.formatters import OutputFormatType
from functools import partial

""" Batch management of media files metadata (tags & artwork)
      . Supported formats:
            'MP3', 'MP4', 'M4A', M4V', 'AIFF', 'ASF', 'QuickTime / MOV',
            'FLAC', 'MonkeysAudio', 'Musepack',
            'Ogg FLAC', 'Ogg Speex', 'Ogg Theora', 'Ogg Vorbis',
            'True Audio', 'WavPack', 'OptimFROG'

            'AVI', 'FLV', 'MKV', 'MKA' (support via FFmpeg)
      . source directory / source file modes
      . include / exclude patterns, etc. (see list of Global Options for details)
      . visualises original / targeted files metadata structure
      . action commands:
          .. print      print media info
          .. set        Set tags in media files,
                        Supports expandable templates:
                          e.g.  <tagger set --title 'The Title, part $track of $tracktotal'>
                          to specify a template value, use the long tag name preceded by $:
                                <tagger set --album 'The Album, ($format)'>, ...
          .. copy       Copies tags from a specified media file
          .. remove     Remove all tags
          .. index      Index Track / Track Total tags
          .. add        TBD: add characters in tags (title, artist, ...)
          .. remove     TBD: remove characters in tags (title, artist, ...)
          .. replace    TBD: regexp-based replace in tags (title, artist, ...)
          .. extract    TBD: extracts artwork

    Usage: tagger [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Global Options (tagger -h for additional help)
        [-r, --recursive]           Recurse into nested folders
        [-el, --endlevel]           End level for recursion into nested folders
        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --alldirs]            Prevent using Include/Exclude patterns on directories
        [-af, --allfiles]           Prevent using Include/Exclude patterns on files
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands (tagger {command} -h for additional help)
        {print, set, copy, remove, index, ...}
"""

class TaggerArgParser(BMPBaseArgParser):
    @staticmethod
    def parse_commands(parser):
        subparsers = parser.add_subparsers(help = 'Tagger commands',
                                            dest='sub_cmd', title = 'Tagger Commands')
        # Print
        print_parser = subparsers.add_parser('print', help = 'Print source directory')
        print_parser.add_argument('-sl', '--startlevel', dest='start_level',
                help = 'Initial nested level for printing (0, i.e. root source directory by default)',
                type = int,
                default = 0)
        print_parser.add_argument('-ss', '--showsize', dest='show_size',
                help ='Shows files size',
                action = 'store_true')
        print_parser.add_argument('-ff', '--fullformat', dest='full_format',
                help ='Shows all media tags',
                action = 'store_true')
        print_parser.add_argument('-st', '--showstats', dest='show_stats',
                help ='Shows media file statistics',
                action = 'store_true')

        # Set Tags
        set_tags_parser = subparsers.add_parser('set', help = 'Sets specified tags in media files')
        set_tags_parser.add_argument('-ti', '--title', dest='title',
                help = "Sets the Title tag",
                type = str)
        set_tags_parser.add_argument('-al', '--album', dest='album',
                help = "Sets the Album tag",
                type = str)
        set_tags_parser.add_argument('-ar', '--artist', dest='artist',
                help = "Sets the Artist tag",
                type = str)
        set_tags_parser.add_argument('-aa', '--albumartist', dest='albumartist',
                help = "Sets the Album Artist tag",
                type = str)
        set_tags_parser.add_argument('-g', '--genre', dest='genre',
                help = "Sets the Genre tag",
                type = str)
        set_tags_parser.add_argument('-c', '--composer', dest='composer',
                help = "Sets the Composer tag",
                type = str)
        set_tags_parser.add_argument('-tr', '--track', dest='track',
                help = "Sets the Track tag",
                type = str)
        set_tags_parser.add_argument('-tt', '--tracktotal', dest='tracktotal',
                help = 'Set the Track Total tag for selected media files',
                type = str)
        set_tags_parser.add_argument('-d', '--disc', dest='disc',
                help = "Sets the Disc tag",
                type = str)
        set_tags_parser.add_argument('-dt', '--disctotal', dest='disctotal',
                help = "Sets the Disctotal tag",
                type = str)
        set_tags_parser.add_argument('-y', '--year', dest='year',
                help = "Sets the Year tag",
                type = str)
        set_tags_parser.add_argument('-art', '--artwork', dest='artwork',
                help = "Sets Artwork: /Path_to_PNG_or_JPEG",
                type = lambda f: BMPBaseArgParser.is_valid_file_path(parser, f))

        set_tags_parser.add_argument('-bm', '--bpm', dest='bpm',
                help = "Sets the BPM tag",
                type = str)
        set_tags_parser.add_argument('-cmp', '--compilaton', dest='compilaton',
                help = "Sets the Compilaton tag",
                type = lambda f: BMPBaseArgParser.is_boolean(parser, f))
        set_tags_parser.add_argument('-grp', '--grouping', dest='grouping',
                help = "Sets the Grouping tag",
                type = str)
        set_tags_parser.add_argument('-com', '--comments', dest='comments',
                help = "Sets the Comments tag",
                type = str)
        set_tags_parser.add_argument('-lr', '--lyrics', dest='lyrics',
                help = "Sets the Lyrics tag",
                type = str)

         # Copy Tags
        copy_tags_parser = subparsers.add_parser('copy', help = 'Copies tags from a specified media file')
        copy_tags_parser.add_argument('-th', '--tagholder', dest='tagholder',
                help = "TagHolder Media file: /Path_to_TagHolder_Media_File",
                type = lambda f: BMPBaseArgParser.is_valid_file_path(parser, f))

         # Remove Tags
        copy_tags_parser = subparsers.add_parser('remove', help = 'Removes all tags')

        # Index
        index_parser = subparsers.add_parser('index',
                                            help = 'Index Tracks for selected media files')
        print_parser.add_argument('-sf', '--startfrom', dest='start_from',
                help = 'A number from which the indexing starts (1 by default)',
                type = int,
                default = 1)


    @staticmethod
    def check_args(args, parser):
        BMPBaseArgParser.check_args(args, parser)

        if not args['sub_cmd']:
            args['sub_cmd'] = 'print'
            args['start_level'] = 0
            args['show_size'] = False
            args['show_stats'] = False
            args['full_format'] = False


class TagsDispatcher:
    @staticmethod
    def print_dir(args):
        BaseTagProcessor().print_dir(src_dir = args['dir'],
                sort = args['sort'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                flatten = False, ensure_uniq = False,
                show_size = args['show_size'], show_stats = args['show_stats'],
                format = OutputFormatType.FULL if args['full_format'] else OutputFormatType.COMPACT)


    @staticmethod
    def set_tags(args):
        tag_holder = TagHolder()
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
        tag_holder.bpm = args['bpm']
        tag_holder.comp = args['compilaton']
        tag_holder.grouping = args['grouping']
        tag_holder.comments = args['comments']
        tag_holder.lyrics = args['lyrics']

        art, art_path = None, args['artwork']
        if art_path:
            with open(os.path.realpath(art_path), 'rb') as f:
                art = f.read()
        if art:
            tag_holder.art = art

        BaseTagProcessor().set_tags_visual(args['dir'],
                sort = args['sort'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                tag_holder = tag_holder, quiet = args['quiet'])


    @staticmethod
    def copy_tags(args):
        BaseTagProcessor().copy_tags(src_dir = args['dir'],
                sort = args['sort'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                tag_holder_path = args['tagholder'], quiet = args['quiet'])

    @staticmethod
    def remove_tags(args):
        BaseTagProcessor().remove_tags(src_dir = args['dir'],
                sort = args['sort'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'], quiet = args['quiet'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'])

    @staticmethod
    def index(args):
        BaseTagProcessor().index(src_dir = args['dir'],
                sort = args['sort'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'])

    @staticmethod
    def dispatch():
        args = TaggerArgParser().parse_options(script_name = 'tagger')
        if args['sub_cmd'] == 'print':
            TagsDispatcher.print_dir(args)
        elif args['sub_cmd'] == 'set':
            TagsDispatcher.set_tags(args)
        elif args['sub_cmd'] == 'index':
            TagsDispatcher.index(args)
        elif args['sub_cmd'] == 'copy':
            TagsDispatcher.copy_tags(args)
        elif args['sub_cmd'] == 'remove':
            TagsDispatcher.remove_tags(args)


def main():
    TagsDispatcher.dispatch()

if __name__ == '__main__':
    main()


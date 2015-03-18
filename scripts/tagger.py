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
          .. print      Prints media info
          .. set        Sets tags in media files, including artwork, e.g:
                                $ tagger set --album 'The Album' -art '~/Desktop/art.jpg'
                            Supports expandable templates. To specify a template value,
                            use the long tag name preceded by $:
                                $ tagger set --title '$title, $track of $tracktotal'
                            In addition to tag fields templates, file names are also supported:
                                $ tagger set --title '$filename'...
          .. copy       Copies tags from a specified media file
          .. remove     Removes tags from media files
          .. index      Indexes Track / Track Total tags
          .. replace    RegExp-based replace in tags (title, artist, ...)
                            e.g., to remove the first three characters in title:
                                $ tagger replace -tf 'title' -fs '^[\s\S]{0,3}' -rs ''
          .. detauch    Extracts artwork

    Usage: tagger [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Global Options (tagger -h for additional help)
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --all-dirs]           Prevent using Include/Exclude patterns on directories
        [-af, --all-files]          Prevent using Include/Exclude patterns on files

        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands (tagger {command} -h for additional help)
        {print, set, copy, remove, index, replace, detauch}
"""

class TaggerArgParser(BMPBaseArgParser):
    SUPPORTED_REPLACE_FIELDS = ['title', 'album', 'artist', 'albumartist', 'composer', 'comments', 'lyrics']

    @staticmethod
    def parse_commands(parser):

        def add_show_other_tags_mode(parser):
            parser.add_argument('-do', '--diff-only', dest = 'diff_tags_only',
                    help ='Show only changed tags in the confirmation propmt',
                    action = 'store_true')

        subparsers = parser.add_subparsers(dest='sub_cmd', title = 'Tagger Commands')

        # Print
        print_parser = subparsers.add_parser('print', description = 'Print source directory')
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
        set_tags_parser = subparsers.add_parser('set', description = 'Sets specified tags in media files. ' \
                                                   'Supports templates, such as $filename, $title, $album, ... ')
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
                type = int)
        set_tags_parser.add_argument('-tt', '--tracktotal', dest='tracktotal',
                help = 'Set the Track Total tag for selected media files',
                type = int)
        set_tags_parser.add_argument('-d', '--disc', dest='disc',
                help = "Sets the Disc tag",
                type = int)
        set_tags_parser.add_argument('-dt', '--disctotal', dest='disctotal',
                help = "Sets the Disctotal tag",
                type = int)
        set_tags_parser.add_argument('-y', '--year', dest='year',
                help = "Sets the Year tag",
                type = int)
        set_tags_parser.add_argument('-en', '--encoder', dest='encoder',
                help = "Sets the Encoder tag",
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
        BMPBaseArgParser.add_display_curent_state(set_tags_parser)
        add_show_other_tags_mode(set_tags_parser)

         # Copy Tags
        copy_tags_parser = subparsers.add_parser('copy', description = 'Copies tags from a specified media file')
        copy_tags_parser.add_argument('-th', '--tagholder', dest='tagholder',
                help = "TagHolder Media file: /Path_to_TagHolder_Media_File",
                type = lambda f: BMPBaseArgParser.is_valid_file_path(parser, f))
        BMPBaseArgParser.add_display_curent_state(copy_tags_parser)
        add_show_other_tags_mode(copy_tags_parser)

         # Remove Tags
        remove_tags_parser = subparsers.add_parser('remove', description = 'Remove tags from media files')
        remove_tags_parser.add_argument('-tf', '--tag-fields', dest='removable_fields',
                help = "Comma-separated list of tag fields to remove",
                type = str)
        BMPBaseArgParser.add_display_curent_state(remove_tags_parser)
        add_show_other_tags_mode(remove_tags_parser)

        # Index
        index_parser = subparsers.add_parser('index', description = 'Index Tracks for selected media files')
        index_parser.add_argument('-sf', '--startfrom', dest='start_from',
                help = 'A number from which the indexing starts, 1 by default',
                type = int,
                default = 1)
        BMPBaseArgParser.add_display_curent_state(index_parser)
        add_show_other_tags_mode(index_parser)

         # Replace Tags
        replace_parser = subparsers.add_parser('replace', description = 'RegExp-based replace in specified tag fields')
        replace_parser.add_argument('-tf', '--tag-field', dest='tag_field',
                help = "A tag field in which to replace. " \
                        "Supported tag fields: {}".format(', '.join(TaggerArgParser.SUPPORTED_REPLACE_FIELDS)),
                type = str,
                required=True)
        replace_parser.add_argument('-fs', '--find-string', dest='find_str',
                help = "Find pattern to look for",
                type = str,
                required=True)
        replace_parser.add_argument('-rs', '--replace-string', dest='replace_str',
                help = "Replace pattern to replace with."\
                        "If not specified and there is a match from the find pattern," \
                        "the entire string will be replaced with that match",
                type = str)
        replace_parser.add_argument('-ic', '--ignorecase', dest='ignore_case',
                help = 'Case insensitive',
                action = 'store_true')
        BMPBaseArgParser.add_display_curent_state(replace_parser)
        add_show_other_tags_mode(replace_parser)

        # Detauch Art
        detauch_parser = subparsers.add_parser('detauch', description = 'Detauches art into specified target directory')
        detauch_parser.add_argument("-td", "--target_dir", dest = "target_dir",
            type = lambda fpath: BMPBaseArgParser.expanded_path(fpath),
            default = None,
            help = "Target directory for detauching art. When omitted, detauched art will be stored in "
                        "the top-level media files source directory")

    @staticmethod
    def check_args(args, parser):
        BMPBaseArgParser.check_args(args, parser)

        if not args['sub_cmd']:
            args['sub_cmd'] = 'print'
            args['show_size'] = False
            args['show_stats'] = False
            args['full_format'] = False

        if args['sub_cmd'] == 'replace':
            if args['tag_field'] not in TaggerArgParser.SUPPORTED_REPLACE_FIELDS:
                parser.error('tagger replace: the field "{0}" is not supported\n\t' \
                             'Supported tag fields: {1}'.format(
                                    args['tag_field'], ', '.join(TaggerArgParser.SUPPORTED_REPLACE_FIELDS)))

        if args['sub_cmd'] == 'index':
            if args['start_from'] < 1:
                parser.error('Track indexing should start from 1, or a larger int number')

        if args['sub_cmd'] == 'detauch':
            if args['target_dir'] is None:
                args['target_dir'] = args['dir']

        if args['sub_cmd'] == 'remove':
            if args['removable_fields'] is not None:
                args['removable_fields'] = [r.strip() for r in args['removable_fields'].split(',')]
                taggable_fields = [field for field in TagHolder.taggable_fields()]
                for removable_field in args['removable_fields']:
                    if removable_field not in (taggable_fields):
                        parser.error('The tag field "{}" is not supported'.format(removable_field))

class TagsDispatcher:
    @staticmethod
    def print_dir(args):
        BaseTagProcessor().print_dir(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                flatten = False, ensure_uniq = False,
                show_size = args['show_size'], show_stats = args['show_stats'],
                format = OutputFormatType.FULL if args['full_format'] else OutputFormatType.COMPACT)


    @staticmethod
    def set_tags(args):
        tag_holder = TagHolder(process_templates = False)
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
        tag_holder.encoder = args['encoder']
        tag_holder.bpm = args['bpm']
        tag_holder.comp = args['compilaton']
        tag_holder.grouping = args['grouping']
        tag_holder.comments = args['comments']
        tag_holder.lyrics = args['lyrics']

        art, art_path = None, args['artwork']
        if art_path:
            with open(art_path, 'rb') as f:
                art = f.read()
        if art:
            tag_holder.art = art

        BaseTagProcessor().set_tags_visual(args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                tag_holder = tag_holder,
                display_current = args['display_current'], quiet = args['quiet'],
                diff_tags_only = args['diff_tags_only'])

    @staticmethod
    def copy_tags(args):
        BaseTagProcessor().copy_tags(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                tag_holder_path = args['tagholder'],
                display_current = args['display_current'], quiet = args['quiet'],
                diff_tags_only = args['diff_tags_only'])

    @staticmethod
    def remove_tags(args):
        BaseTagProcessor().remove_tags(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                display_current = args['display_current'], quiet = args['quiet'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                nullable_fields = args['removable_fields'],
                diff_tags_only = args['diff_tags_only'])

    @staticmethod
    def index(args):
        BaseTagProcessor().index(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                display_current = args['display_current'], quiet = args['quiet'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                diff_tags_only = args['diff_tags_only'], start_from = args['start_from'])

    @staticmethod
    def replace_tags(args):
        BaseTagProcessor().replace_tag(args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                display_current = args['display_current'], quiet = args['quiet'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                tag_field = args['tag_field'], ignore_case = args['ignore_case'],
                find_str = args['find_str'], replace_str = args['replace_str'],
                diff_tags_only = args['diff_tags_only'])

    @staticmethod
    def detauch_art(args):
        BaseTagProcessor().detauch_art(args['dir'],
                sort = args['sort'],
                end_level = args['end_level'],
                display_current = args['display_current'], quiet = args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                target_dir = args['target_dir'])

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
        elif args['sub_cmd'] == 'replace':
            TagsDispatcher.replace_tags(args)
        elif args['sub_cmd'] == 'detauch':
            TagsDispatcher.detauch_art(args)

def main():
    TagsDispatcher.dispatch()

if __name__ == '__main__':
    main()


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
      . display sorting:
          .. by size/date, ascending/descending
      . action commands:
          .. print      Prints media files
          .. set        Sets tags in media files, including artwork, e.g:
                                $ tagger set --album 'The Album' -art '~/Desktop/art.jpg'
                            Supports expandable templates. To specify a template value,
                            use the long tag field name preceded by $:
                                $ tagger set --title '$title, $track of $tracktotal'
                            In addition to tag fields templates, file system names are also supported:
                                $ tagger set --title '$filename' --album '$dirname' --artist '$pardirname'...
          .. copy       Copies tags from a specified media file
          .. index      Indexes Track / Track Total tags
          .. remove     Removes tags from media files
          .. replace    RegExp-based replace in specified tags
                          e.g., to remove the first three characters in title:
                                $ tagger replace -tf 'title' -fs '^[\s\S]{0,3}' -rs ''
          .. capitalize Capitalizes words in specified tags
          .. detauch    Extracts artwork

    Usage: tagger [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
      Input source mode:
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Recursion mode:
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

      Filter files or folders:
        [-in, --include]            Include: Unix-style name patterns separated by ';'
        [-sh, --show-hidden]        Shows hidden files
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
        {print, set, copy, index, remove, replace, capitalize, detauch, version, info}
        $ tagger {command} -h #run this for detailed help on individual commands
"""

from batchmp.cli.base.bmp_options import BatchMPArgParser, BatchMPHelpFormatter, BatchMPBaseCommands
from batchmp.tags.handlers.tagsholder import TagHolder
from batchmp.fstools.fsutils import FSH
from batchmp.fstools.builders.fsentry import FSEntryDefaults

class TaggerCommands(BatchMPBaseCommands):
    SET = 'set'
    COPY = 'copy'
    INDEX = 'index'
    REMOVE = 'remove'
    REPLACE = 'replace'
    CAPITALIZE = 'capitalize'
    DETAUCH = 'detauch'

    @classmethod
    def commands_meta(cls):
        return ''.join(('{',
                        '{}, '.format(cls.PRINT),
                        '{}, '.format(cls.SET),
                        '{}, '.format(cls.COPY),
                        '{}, '.format(cls.INDEX),
                        '{}, '.format(cls.REMOVE),
                        '{}, '.format(cls.REPLACE),
                        '{}, '.format(cls.CAPITALIZE),
                        '{}, '.format(cls.DETAUCH),
                        '{}, '.format(cls.INFO),
                        '{}'.format(cls.VERSION),
                        '}'))


class TaggerArgParser(BatchMPArgParser):
    ''' Tagger Commands parsing
    '''
    SUPPORTED_TEXTUAL_TAGGABLE_FIELDS = [field for field in sorted(TagHolder.textual_fields())]
    SUPPORTED_TAGGABLE_FIELDS = [field for field in sorted(TagHolder.taggable_fields())]

    def __init__(self):
        self._script_name = 'Tagger'
        self._description =  \
        '''
        Tagger manages media metadata, such as tags and
        artwork. It can read and write metadata across
        many different formats, with support for advanced
        metadata manipulation such as regexp-based replace
        in tags, expandable template processing, etc.

        As default behavior, Tagger first visualises targeted
        changes and ask for confirmation before actually
        changing anything.
        '''

    # Args parsing
    def parse_commands(self, parser):
        ''' parses Tagger commands
        '''
        def _add_arg_diff_tags_only_mode(parser):
            parser.add_argument('-do', '--diff-only', dest = 'diff_tags_only',
                    help ='Show only changed tags in the confirmation propmt',
                    action = 'store_true')

        subparsers = parser.add_subparsers(dest='sub_cmd',
                                                title = 'Tagger Commands',
                                                        metavar = TaggerCommands.commands_meta())
        self._add_version(subparsers)
        self._add_info(subparsers)

        # Print
        print_parser = subparsers.add_parser(TaggerCommands.PRINT,
                                            description = 'Prints info about media files metadata, such as tags and artwork',
                                            formatter_class = BatchMPHelpFormatter)
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
        set_tags_parser = subparsers.add_parser(TaggerCommands.SET,
                                    description = 'Sets specified tags in media files. ' \
                                                   'Supports expandable templates, such as $filename, $dirname, $pardirname, $title, $album, ... ',
                                    formatter_class = BatchMPHelpFormatter)
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
                help = "Sets Artwork Image from file path or URL",
                type = lambda fpath: self._is_valid_url_or_file_path(parser, fpath))
        set_tags_parser.add_argument('-bm', '--bpm', dest='bpm',
                help = "Sets the BPM tag",
                type = str)
        set_tags_parser.add_argument('-cmp', '--compilaton', dest='compilaton',
                help = "Sets the Compilaton tag",
                type = lambda fpath: self._is_boolean(parser, fpath))
        set_tags_parser.add_argument('-grp', '--grouping', dest='grouping',
                help = "Sets the Grouping tag",
                type = str)
        set_tags_parser.add_argument('-com', '--comments', dest='comments',
                help = "Sets the Comments tag",
                type = str)
        set_tags_parser.add_argument('-lr', '--lyrics', dest='lyrics',
                help = "Sets the Lyrics tag",
                type = str)
        self._add_arg_display_curent_state_mode(set_tags_parser)
        _add_arg_diff_tags_only_mode(set_tags_parser)

         # Copy Tags
        copy_tags_parser = subparsers.add_parser(TaggerCommands.COPY,
                                    description = 'Copies tags from a specified media file',
                                    formatter_class = BatchMPHelpFormatter)
        copy_tags_parser.add_argument('-th', '--tagholder', dest='tagholder',
                help = "TagHolder Media file: /Path_to_TagHolder_Media_File",
                required = True,
                type = lambda fpath: self._is_valid_file_path(parser, fpath))
        self._add_arg_display_curent_state_mode(copy_tags_parser)
        _add_arg_diff_tags_only_mode(copy_tags_parser)

        # Index
        index_parser = subparsers.add_parser(TaggerCommands.INDEX,
                                    description = 'Index Tracks for selected media files',
                                    formatter_class = BatchMPHelpFormatter)
        index_parser.add_argument('-sf', '--startfrom', dest='start_from',
                help = 'A number from which the indexing starts, 1 by default',
                type = int,
                default = 1)
        self._add_arg_display_curent_state_mode(index_parser)
        _add_arg_diff_tags_only_mode(index_parser)

         # Remove Tags
        remove_tags_parser = subparsers.add_parser(TaggerCommands.REMOVE,
                                    description = 'Remove tags from media files',
                                    formatter_class = BatchMPHelpFormatter)
        remove_tags_parser.add_argument('-tf', '--tag-fields', dest='tag_fields',
                help = "Comma-separated list of tag fields to remove. " \
                        "Supported tag fields: {}".format(', '.join(self.SUPPORTED_TAGGABLE_FIELDS)),
                type = str)
        self._add_arg_display_curent_state_mode(remove_tags_parser)
        _add_arg_diff_tags_only_mode(remove_tags_parser)

         # Replace Tags
        replace_parser = subparsers.add_parser(TaggerCommands.REPLACE,
                                    description = 'RegExp-based replace in specified tag fields',
                                    formatter_class = BatchMPHelpFormatter)
        replace_parser.add_argument('-tf', '--tag-fields', dest='tag_fields',
                help = "Comma-separated list of tag fields in which to replace. " \
                        "Supported tag fields: {}".format(', '.join(self.SUPPORTED_TEXTUAL_TAGGABLE_FIELDS)),
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
        self._add_arg_display_curent_state_mode(replace_parser)
        _add_arg_diff_tags_only_mode(replace_parser)

         # Capitalize Tags
        capitalize_parser = subparsers.add_parser(TaggerCommands.CAPITALIZE,
                                    description = 'Capitalize words in specified tag fields',
                                    formatter_class = BatchMPHelpFormatter)
        capitalize_parser.add_argument('-tf', '--tag-fields', dest='tag_fields',
                help = "Comma-separated list of tag fields in which to capitalize words. " \
                        "Supported tag fields: {}".format(', '.join(self.SUPPORTED_TEXTUAL_TAGGABLE_FIELDS)),
                type = str,
                required=True)
        self._add_arg_display_curent_state_mode(capitalize_parser)
        _add_arg_diff_tags_only_mode(capitalize_parser)

        # Detauch Art
        detauch_parser = subparsers.add_parser(TaggerCommands.DETAUCH,
                                    description = 'Detauches art into specified target directory',
                                    formatter_class = BatchMPHelpFormatter)
        detauch_parser.add_argument("-td", "--target_dir", dest = "target_dir",
            type = lambda fpath: FSH.full_path(fpath),
            default = None,
            help = "Target directory for detauching art. When omitted, detauched art will be stored in "
                        "the top-level media files source directory")

    # Args Checking
    def default_command(self, args, parser):
        args['sub_cmd'] = TaggerCommands.PRINT
        args['start_level'] = 0
        args['show_size'] = False
        args['show_stats'] = False
        args['full_format'] = False

    def check_args(self, args, parser):
        super().check_args(args, parser)

        def parse_tag_fields(fields, supported_fields):
            fields = [r.strip() for r in fields.split(',')]
            for tag_field in fields:
                if tag_field not in supported_fields:
                    parser.error('The tag field "{0}" is not supported\n\t' \
                                'Supported tag fields: {1}'.format(tag_field, ', '.join(supported_fields)))
            return fields

        # only consider playable media files by default
        if args['file_type'] == FSEntryDefaults.DEFAULT_FILE_TYPE:
            args['file_type'] = FSEntryDefaults.DEFAULT_MEDIA_TYPE

        if args['sub_cmd'] == TaggerCommands.INDEX:
            if args['start_from'] < 1:
                parser.error('Track indexing should start from 1, or a larger int number')

        elif args['sub_cmd'] == TaggerCommands.REMOVE:
            if args['tag_fields'] is not None:
                args['tag_fields'] = parse_tag_fields(args['tag_fields'], \
                                                      self.SUPPORTED_TAGGABLE_FIELDS)

        elif args['sub_cmd'] in (TaggerCommands.REPLACE, TaggerCommands.CAPITALIZE):
            args['tag_fields'] = parse_tag_fields(args['tag_fields'], \
                                                      self.SUPPORTED_TEXTUAL_TAGGABLE_FIELDS)

        elif args['sub_cmd'] == TaggerCommands.DETAUCH:
            if args['target_dir'] is None:
                args['target_dir'] = args['dir']

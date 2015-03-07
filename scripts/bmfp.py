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

import sys
from datetime import timedelta
from batchmp.ffmptools.ffcommands.convert import Convertor
from batchmp.ffmptools.ffcommands.segment import Segmenter
from batchmp.ffmptools.ffcommands.fragment import Fragmenter
from batchmp.ffmptools.ffcommands.denoise import Denoiser
from scripts.base.bmpbargp import BMPBaseArgParser

""" Batch processing of media files
      . Uses multiprocessing to utilize available CPU cores
      . supports source directory / source file modes
      . supports recursion to specified end_level
      . allows for include / exclude patterns (Unix style)
      . action commands:
          .. convert        Converts media to specified format
          .. segment        Splits media files into segments
          .. fragment       Extract a media file fragment
          .. denoise        Reduces background audio noise in media files
          .. speed up       TDB: Uses Time Stretching to increase audio / video speed
          .. slow down      TDB: Uses Time Stretching to increase audio / video speed
          .. adjust volume  TDB: Adjust audio volume
          .. detauch        TDB: Detauch streams from original media

    Usage: bmfp [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Global Options (bmfp -h for additional help)
        [-r, --recursive]           Recurse into nested folders
        [-el, --endlevel]           End level for recursion into nested folders
        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --alldirs]            Prevent using Include/Exclude patterns on directories
        [-af, --allfiles]           Prevent using Include/Exclude patterns on files
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-q, --quiet]               Do not visualise changes / show messages during processing

        [-se, --serial-exec]        Run all task's commands in a single process
        [-nb, --no-backup]          Do not backup the original file

      Commands: (bmfp {command} -h for additional help)
        {convert, segment, fragment, denoise, ...}
"""

class BMFPArgParser(BMPBaseArgParser):
    DEFAULT_CONVERSION_OPTIONS = '-q:v 0 -q:a 0'

    @staticmethod
    def parse_commands(parser):
        # BFMP Global
        misc_group = parser.add_argument_group('Commands Execution')
        misc_group.add_argument("-se", "--serial-exec", dest='serial_exec',
                    help = "Runs all task's commands in a single process",
                    action='store_true')
        misc_group.add_argument("-nb", "--no-backup", dest='nobackup',
                    help = "Do not backup the original file",
                    action='store_true')

        # Commands
        subparsers = parser.add_subparsers(help = 'BMFP commands',
                                            dest='sub_cmd', title = 'BMFP Commands')

        # Convert
        convert_parser = subparsers.add_parser('convert', help = 'Convert media to specified format')
        convert_parser.add_argument('-tf', '--target_format', dest='target_format',
                help = 'Target format file extension, e.g. mp3 / m4a / mp4 / mov /...',
                type = str,
                required = True)
        group = convert_parser.add_argument_group('Conversion Options')
        group.add_argument('-co', '--convert-options', dest='convert_options',
                help = 'FFmpeg conversion options. When specified, overrides all other option switches',
                type = str,
                default = BMFPArgParser.DEFAULT_CONVERSION_OPTIONS)
        group.add_argument('-la', '--lossless-audio', dest='lossless_audio',
                help = 'For media formats with support for lossless audio, tries a lossless conversion',
                action='store_true')
        group.add_argument('-cc', '--change-container', dest='change_container',
                help = 'Changes media container without actual re-encoding of contained streams'
                       'Takes priority over all other option switches, except for explicit "--convert-options"',
                action='store_true')

        # Denoise
        denoise_parser = subparsers.add_parser('denoise', help = 'Reduces background audio noise in media files via filtering out highpass / low-pass frequencies')
        denoise_parser.add_argument('-np', '--numpasses', dest='num_passes',
                help = 'Applies filters in multiple passes',
                type = int,
                default = 1)

        group = denoise_parser.add_argument_group('Pass Filters')
        group.add_argument("-hp", "--highpass", dest='highpass',
                    help = "Cutoff boundary for lower frequencies",
                    type = int,
                    default = 200)
        group.add_argument("-lp", "--lowpass", dest='lowpass',
                    help = "Cutoff boundary for higher frequencies",
                    type = int,
                    default = 3000)

        # Fragment
        fragment_parser = subparsers.add_parser('fragment', help = 'Extracts a fragment via specified start time & duration')
        group = fragment_parser.add_argument_group('Fragment parameters')
        group.add_argument('-s', '--starttime', dest='fragment_starttime',
                help = 'Fragment start time, in seconds or in the "hh:mm:ss[.xxx]" format',
                type = lambda f: BMPBaseArgParser.is_timedelta(parser, f),
                required = True)
        group.add_argument('-d', '--duration', dest='fragment_duration',
                help = 'Fragment duration, in seconds or in the "hh:mm:ss[.xxx]" format',
                type = lambda f: BMPBaseArgParser.is_timedelta(parser, f),
                default = timedelta(days = 380))
        fragment_parser.add_argument("-ro", "--replace-original", dest='replace_original',
                    help = "Replace original file with the fragment",
                    action='store_true')

        # Segment
        segment_parser = subparsers.add_parser('segment', help = 'Segments media by duration or file size')
        segment_group = segment_parser.add_mutually_exclusive_group()
        segment_group.add_argument('-fs', '--filesize', dest='segment_filesize',
                help = 'Maximum media file size in MB',
                type = int,
                default = 0)
        segment_group.add_argument('-d', '--duration', dest='segment_duration',
                help = 'Maximum media duration, in seconds or in the "hh:mm:ss[.xxx]" format',
                type = lambda f: BMPBaseArgParser.is_timedelta(parser, f),
                default = timedelta(0))


    @staticmethod
    def check_args(args, parser):
        if not args['sub_cmd']:
            parser.print_help()
            sys.exit(1)

        # Global options check
        BMPBaseArgParser.check_args(args, parser)

        # Segment attributes check
        if args['sub_cmd'] is 'segment':
            if args['segment_filesize'] is 0 and args['segment_duration'] is timedelta(0):
                parser.error('bmfp segment:\n\t'
                             'One of the command parameters needs to be specified: <filesize | duration>')

        elif args['sub_cmd'] is 'convert':
            # Convert attributes check
            if args['convert_options'] is BMFPArgParser.DEFAULT_CONVERSION_OPTIONS:
                if args['lossless_audio']:
                    args['convert_options'] = '-q:v 0 -acodec alac'

                if args['change_container']:
                    args['convert_options'] = '-c copy -copyts'

        '''
        if not args['sub_cmd']:
            args['sub_cmd'] = 'convert'
            args['target_format'] = 'm4a'
            args['convert_options'] = '-q:v 0 -q:a 0'
            args['lossless_audio'] = False
            args['change_container'] = False
            args['dir'] = '/Users/AKPower/Desktop/music/samples/convert/test'
            args['nobackup'] = False


            if not args['sub_cmd']:
                args['sub_cmd'] = 'fragment'
                args['fragment_starttime'] = timedelta(seconds = 10)
                args['fragment_duration'] = timedelta(days = 380)
                args['nobackup'] = False

            if not args['sub_cmd']:
                args['sub_cmd'] = 'segment'
                args['segment_filesize'] = 40
                args['segment_duration'] = timedelta(minutes = 4, seconds = 10)
                args['nobackup'] = False

                args['dir'] = '/Users/AKPower/Desktop/music/samples/test'
        '''


class BMFPDispatcher:
    @staticmethod
    def convert(args):
        Convertor().convert(src_dir = args['dir'],
                sort = args['sort'], end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                backup = not args['nobackup'], serial_exec = args['serial_exec'],
                target_format = args['target_format'], convert_options = args['convert_options'])

    @staticmethod
    def segment(args):
        Segmenter().segment(src_dir = args['dir'],
                sort = args['sort'], end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                segment_size_MB = args['segment_filesize'],
                segment_length_secs = args['segment_duration'].total_seconds(),
                backup = not args['nobackup'], serial_exec = args['serial_exec'])

    @staticmethod
    def fragment(args):
        Fragmenter().fragment(src_dir = args['dir'],
                sort = args['sort'], end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                fragment_starttime = args['fragment_starttime'].total_seconds(),
                fragment_duration = args['fragment_duration'].total_seconds(),
                backup = not args['nobackup'], serial_exec = args['serial_exec'],
                replace_original = args['replace_original'])

    @staticmethod
    def denoise(args):
        Denoiser().apply_af_filters(src_dir = args['dir'],
                sort = args['sort'], end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['all_dirs'], filter_files = not args['all_files'],
                num_passes=args['numpasses'], highpass=args['highpass'], lowpass=args['lowpass'],
                backup = not args['nobackup'])


    @staticmethod
    def dispatch():
        args = BMFPArgParser().parse_options(script_name = 'bmfp')

        if args['sub_cmd'] == 'convert':
            BMFPDispatcher.convert(args)
        if args['sub_cmd'] == 'denoise':
            BMFPDispatcher.denoise(args)
        elif args['sub_cmd'] == 'fragment':
            BMFPDispatcher.fragment(args)
        elif args['sub_cmd'] == 'segment':
            BMFPDispatcher.segment(args)

def main():
    BMFPDispatcher.dispatch()

if __name__ == '__main__':
    main()



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


""" Batch processing of media files
      . Uses multiprocessing to utilize available CPU cores
      . supports source directory / source file modes
      . supports recursion to specified end_level
      . allows for include / exclude patterns (Unix style)
      . action commands:
          .. convert        Converts media to specified format
                                For example, to convert all files in current directory
                                    $ bmfp -pm convert -la -tf FLAC
          .. segment        Splits media files into segments
                                For example, to split media files in segments of 45 mins:
                                    $ bmfp segment -d 45:00
          .. fragment       Extract a media file fragment
          .. denoise        Reduces background audio noise in media files
          .. speed up       TDB: Uses Time Stretching to increase audio / video speed
          .. slow down      TDB: Uses Time Stretching to increase audio / video speed
          .. adjust volume  TDB: Adjust audio volume

    Usage: bmfp [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
      Input source mode:
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Recursion mode:
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

      Filter files or folders:
        [-in, --include]            Include: Unix-style name patterns separated by ';'
        [-ex, --exclude]            Exclude: Unix-style name patterns separated by ';'
        [-fd, --filter-dirs]        Enable  Include/Exclude patterns on directories
        [-af, --all-files]          Disable Include/Exclude patterns on files

      Miscellaneous:
        [-q, --quiet]               Do not visualise changes / show messages during processing

      FFmpeg General Options:
        [-ma, --map-all]            Force including all streams from the input file
        [-cc, --copy-codecs]        Copy streams codecs without re-encoding
        [-vn, --no-video]           Exclude video streams from the output
        [-an, --no-audio]           Exclude audio streams from the output
        [-sn, --no-subs]            Exclude subtitles streams from the output
        [-fo, --ffmpeg-options]     Additional FFmpeg options

      FFmpeg Commands Execution:
        [-pm, --preserve-meta]      Preserve metadata of processed files
        [-se, --serial-exec]        Run all task's commands in a single process
        [-nb, --no-backup]          Do not backup the original file

      Commands:
        {convert, denoise, fragment, segment, ...}
        $ bmfp {command} -h  #run this for detailed help on individual commands
"""
import sys
from datetime import timedelta
from scripts.base.bmpbs import BMPBaseArgParser
from batchmp.ffmptools.ffcommands.convert import Convertor
from batchmp.ffmptools.ffcommands.segment import Segmenter
from batchmp.ffmptools.ffcommands.fragment import Fragmenter
from batchmp.ffmptools.ffcommands.denoise import Denoiser
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands, FFmpegBitMaskOptions

class BMFPArgParser(BMPBaseArgParser):
    ''' BMFP commands parsing
    '''
    @staticmethod
    def add_arg_misc_group(parser):
        misc_group = parser.add_argument_group('Miscellaneous')
        misc_group.add_argument("-q", "--quiet", dest = 'quiet',
                    help = "Disable visualising changes & displaying info messages during processing",
                    action = 'store_true')

    @classmethod
    def parse_commands(cls, parser):
        ''' parses BMFP parsing
        '''

        # BFMP Global options
        ffmpeg_group = parser.add_argument_group('FFmpeg General Options')
        ffmpeg_group.add_argument("-ma", "--map-all", dest='all_streams',
                    help = "Force including all streams from the input file",
                    action='store_true')
        ffmpeg_group.add_argument("-cc", "--copy-codecs", dest='copy_codecs',
                    help = "Copy streams codecs without re-encoding",
                    action='store_true')
        ffmpeg_group.add_argument("-vn", "--no-video", dest='exclude_video',
                    help = "Exclude video streams from the output",
                    action='store_true')
        ffmpeg_group.add_argument("-an", "--no-audio", dest='exclude_audio',
                    help = "Exclude audio streams from the output",
                    action='store_true')
        ffmpeg_group.add_argument("-sn", "--no-subs", dest='exclude_subtitles',
                    help = "Exclude subtitles streams from the output",
                    action='store_true')
        ffmpeg_group.add_argument('-fo', '--ffmpeg-options', dest='ff_other_options',
                help = 'Additional options for running FFmpeg',
                type = str)

        misc_group = parser.add_argument_group('FFmpeg Commands Execution')
        misc_group.add_argument("-pm", "--preserve-meta", dest='preserve_metadata',
                    help = "Preserve metadata of processed files",
                    action='store_true')
        misc_group.add_argument("-se", "--serial-exec", dest='serial_exec',
                    help = "Runs all task's commands in a single process",
                    action='store_true')
        misc_group.add_argument("-nb", "--no-backup", dest='nobackup',
                    help = "Do not backup the original file",
                    action='store_true')

        # Commands
        subparsers = parser.add_subparsers(dest='sub_cmd', title = 'BMFP Commands')

        # Convert
        convert_parser = subparsers.add_parser('convert', description = 'Converts media to specified format')
        convert_parser.add_argument('-tf', '--target-format', dest='target_format',
                help = 'Target format file extension, e.g. mp3 / m4a / mp4 / mov /...',
                type = str,
                required = True)
        group = convert_parser.add_argument_group('Conversion Options')
        group.add_argument('-co', '--convert-options', dest='convert_options',
                help = 'FFmpeg conversion options. When specified, override all other conversion option switches',
                type = str,
                default = FFmpegCommands.CONVERT_COPY_VBR_QUALITY)
        group.add_argument('-cc', '--change-container', dest='change_container',
                help = 'Changes media container without actual re-encoding of contained streams. When specified, ' \
                       'takes priority over all other option switches except for explicit "--convert-options"',
                action='store_true')
        group.add_argument('-la', '--lossless-audio', dest='lossless_audio',
                help = 'For media formats with support for lossless audio, tries a lossless conversion',
                action='store_true')

        # Denoise
        denoise_parser = subparsers.add_parser('denoise', description = 'Reduces background audio noise in media files via filtering out highpass / low-pass frequencies')
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
        fragment_parser = subparsers.add_parser('fragment', description = 'Extracts a fragment via specified start time & duration')
        group = fragment_parser.add_argument_group('Fragment parameters')
        group.add_argument('-fs', '--starttime', dest='fragment_starttime',
                help = 'Fragment start time, in seconds or in the "hh:mm:ss[.xxx]" format',
                type = lambda f: cls.is_timedelta(parser, f),
                required = True)
        group.add_argument('-fd', '--duration', dest='fragment_duration',
                help = 'Fragment duration, in seconds or in the "hh:mm:ss[.xxx]" format',
                type = lambda f: cls.is_timedelta(parser, f),
                default = timedelta(days = 380))
        fragment_parser.add_argument("-ro", "--replace-original", dest='replace_original',
                    help = "Replace original file with the fragment",
                    action='store_true')

        # Segment
        segment_parser = subparsers.add_parser('segment', description = 'Segments media by specified maximum duration or file size')
        segment_group = segment_parser.add_mutually_exclusive_group()
        segment_group.add_argument('-fs', '--filesize', dest='segment_filesize',
                help = 'Maximum media file size in MB',
                type = float,
                default = 0.0)
        segment_group.add_argument('-sd', '--duration', dest='segment_duration',
                help = 'Maximum media duration, in seconds or in the "hh:mm:ss[.xxx]" format',
                type = lambda f: cls.is_timedelta(parser, f),
                default = timedelta(0))
        segment_parser.add_argument("-rt", "--reset-timestamps", dest='reset_timestamps',
                    help = "Reset timestamps at the begin of each segment, so that it "
                            "starts with near-zero timestamps and therefore there are minimum pauses "
                            "betweeen segments when played one after another. "
                            "May not work well for some formats / combinations of muxers/codecs",
                    action='store_true')


    @classmethod
    def check_args(cls, args, parser):
        ''' Validation of supplied BMFP CLI arguments
        '''
        if not args['sub_cmd']:
            parser.print_help()
            sys.exit(1)

        # Global options check
        super().check_args(args, parser)

        # Compile FF global options
        ff_global_options = 0
        if args['all_streams']:
            ff_global_options |= FFmpegBitMaskOptions.MAP_ALL_STREAMS
        if args['copy_codecs']:
            ff_global_options |= FFmpegBitMaskOptions.COPY_CODECS
        if args['exclude_video']:
            ff_global_options |= FFmpegBitMaskOptions.DISABLE_VIDEO
        if args['exclude_audio']:
            ff_global_options |= FFmpegBitMaskOptions.DISABLE_AUDIO
        if args['exclude_subtitles']:
            ff_global_options |= FFmpegBitMaskOptions.DISABLE_SUBTITLES

        args['ff_global_options'] = ff_global_options

        # Segment attributes check
        if args['sub_cmd'] == 'segment':
            if not args['segment_filesize'] and not args['segment_duration'].total_seconds():
                parser.error('bmfp segment:\n\t'
                             'One of the command parameters needs to be specified: <filesize | duration>')

        elif args['sub_cmd'] == 'convert':
            # Convert attributes check
            args['target_format'] = args['target_format'].lower()
            if not args['target_format'].startswith('.'):
                args['target_format'] = '.{}'.format(args['target_format'])

            if args['convert_options'] == FFmpegCommands.CONVERT_COPY_VBR_QUALITY: #default
                if args['lossless_audio']:
                    if args['target_format'] == '.flac':
                        args['convert_options'] = FFmpegCommands.CONVERT_LOSSLESS_FLAC
                    elif args['target_format'] == '.m4a':
                        args['convert_options'] = FFmpegCommands.CONVERT_LOSSLESS_ALAC

                if args['change_container']:
                    args['convert_options'] = FFmpegCommands.CONVERT_CHANGE_CONTAINER


class BMFPDispatcher:
    ''' BMFP CLI commands Dispatcher
    '''
    @staticmethod
    def convert(args):
        Convertor().convert(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                backup = not args['nobackup'], serial_exec = args['serial_exec'],
                target_format = args['target_format'], convert_options = args['convert_options'],
                ff_global_options = args['ff_global_options'], ff_other_options = args['ff_other_options'],
                preserve_metadata = args['preserve_metadata'])

    @staticmethod
    def denoise(args):
        Denoiser().apply_af_filters(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                num_passes=args['num_passes'], highpass=args['highpass'], lowpass=args['lowpass'],
                backup = not args['nobackup'],
                ff_global_options = args['ff_global_options'], ff_other_options = args['ff_other_options'],
                preserve_metadata = args['preserve_metadata'])

    @staticmethod
    def fragment(args):
        Fragmenter().fragment(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                fragment_starttime = args['fragment_starttime'].total_seconds(),
                fragment_duration = args['fragment_duration'].total_seconds(),
                backup = not args['nobackup'], serial_exec = args['serial_exec'],
                replace_original = args['replace_original'],
                ff_global_options = args['ff_global_options'], ff_other_options = args['ff_other_options'],
                preserve_metadata = args['preserve_metadata'])

    @staticmethod
    def segment(args):
        Segmenter().segment(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                segment_size_MB = args['segment_filesize'],
                segment_length_secs = args['segment_duration'].total_seconds(),
                backup = not args['nobackup'], serial_exec = args['serial_exec'],
                ff_global_options = args['ff_global_options'], ff_other_options = args['ff_other_options'],
                reset_timestamps = args['reset_timestamps'],
                preserve_metadata = args['preserve_metadata'])

    @staticmethod
    def dispatch():
        ''' Dispatches BMFP commands
        '''
        args = BMFPArgParser.parse_options(script_name = 'bmfp', description = \
                        '''
                        BMFP allows for efficient media processing,
                        such as conversion between various formats,
                        segmenting / fragmenting media files, denoising audio,
                        detaching individual audio / video streams, etc.
                        BMFP is built on top of FFmpeg (http://ffmpeg.org/),
                        which needs to be installed and available in the command line.
                        ''')

        if args['sub_cmd'] == 'convert':
            BMFPDispatcher.convert(args)
        if args['sub_cmd'] == 'denoise':
            BMFPDispatcher.denoise(args)
        elif args['sub_cmd'] == 'fragment':
            BMFPDispatcher.fragment(args)
        elif args['sub_cmd'] == 'segment':
            BMFPDispatcher.segment(args)

def main():
    ''' BMFP entry point
    '''
    BMFPDispatcher.dispatch()

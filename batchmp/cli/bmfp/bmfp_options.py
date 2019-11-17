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
          .. print          Prints media files
          .. convert        Converts media to specified format
                                For example, to convert all files in current directory
                                    $ bmfp convert -la -tf FLAC
          .. normalize      Nomalizes sound volume in media files
                                Peak normalization supported, RMS normalizations TBD
          .. fragment       Extract a media file fragment
          .. segment        Splits media files into segments
                                For example, to split media files in segments of 45 mins:
                                    $ bmfp segment -d 45:00
          .. silencesplit   Splits media files into segments via detecting specified silence
                                    $ bmfp silencesplit

          .. cuesplit       Splits media files into parts with specified output format,
                            according to their respective cue sheets
                                For example, to split all cue files in the current directory
                                    $ bmfp cuesplit -tf mp3

          .. denoise        Reduces background audio noise in media files

          .. adjust volume  TDB: Adjust audio volume
          .. speed up       TDB: Uses Time Stretching to increase audio / video speed
          .. slow down      TDB: Uses Time Stretching to increase audio / video speed

    Usage: bmfp [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
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

        Target output Directory     Target output directory. When omitted, will be
        [-td, --target-dir]         automatically created at the parent level of
                                    the input source. For recursive processing,
                                    the processed files directory structure there
                                    will be the same as for the original files.
      FFmpeg General Output Options:
        [-ma, --map-all]            Force including all streams from the input file
        [-cc, --copy-codecs]        Copy streams codecs without re-encoding
        [-vn, --no-video]           Exclude video streams from the output
        [-an, --no-audio]           Exclude audio streams from the output
        [-sn, --no-subs]            Exclude subtitles streams from the output
        [-fo, --ffmpeg-options]     Additional FFmpeg options

      FFmpeg Commands Execution:
        [-q, --quiet]               Do not visualise changes / show messages during processing
        [-se, --serial-exec]        Run all task's commands in a single process

      Commands:
        {print, convert, normalize, fragment, segment, silencesplit, cuesplit, denoise, version, info}
        $ bmfp {command} -h  #run this for detailed help on individual commands
"""
import os, sys, argparse
from datetime import timedelta
from batchmp.cli.base.bmp_options import BatchMPArgParser, BatchMPHelpFormatter, BatchMPBaseCommands
from batchmp.ffmptools.ffrunner import LogLevel
from batchmp.ffmptools.ffcommands.silencesplit import SilenceSplitter
from batchmp.ffmptools.ffcommands.denoise import Denoiser
from batchmp.ffmptools.ffutils import FFH, FFmpegNotInstalled, FFHDefaults
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands, FFmpegBitMaskOptions
from batchmp.fstools.builders.fsentry import FSEntryDefaults

class BMFPCommands(BatchMPBaseCommands):
    CONVERT = 'convert'
    NORMALIZE = 'normalize'
    FRAGMENT = 'fragment'
    SEGMENT = 'segment'
    SILENCESPLIT = 'silencesplit'
    CUESPLIT = 'cuesplit'
    DENOISE = 'denoise'

    @classmethod
    def commands_meta(cls):
        return ''.join(('{',
                        '{}, '.format(cls.PRINT),
                        '{}, '.format(cls.CONVERT),
                        '{}, '.format(cls.NORMALIZE),
                        '{}, '.format(cls.FRAGMENT),
                        '{}, '.format(cls.SEGMENT),
                        '{}, '.format(cls.SILENCESPLIT),
                        '{}, '.format(cls.CUESPLIT),
                        '{}, '.format(cls.DENOISE),
                        '{}, '.format(cls.INFO),
                        '{}'.format(cls.VERSION),
                        '}'))


class BMFPArgParser(BatchMPArgParser):
    ''' BMFP commands parsing
    '''
    def __init__(self):
        self._script_name = 'BMFP'
        self._description = \
        '''
        BMFP is a batch audio/video media processor for
        efficient media content transformations across
        selected media files. BMFP supports operations
        such as batch conversion between various formats,
        normalization of audio volume,
        segmenting / fragmenting media, denoising audio,
        detaching individual audio / video streams, etc.

        BMFP is built on top of FFmpeg (http://ffmpeg.org/),
        which needs to be installed and available
        in the command line.
        '''

    # Args Parsing
    def parse_commands(self, parser):
        ''' BMFP commands parsing
        '''

        # BFMP Global options
        target_output_group = parser.add_argument_group('Target Output Directory')
        target_output_group.add_argument("-td", "--target-dir", dest = "target_dir",
                    type = lambda d: self._is_valid_dir_path(parser, d),
                    help = "Target output directory. When omitted, will be automatically "
                            "created at the parent level of the input source. "
                            "For recursive processing, the processed files directory structure there "
                            "will be the same as for the original files.")

        ffmpeg_group = parser.add_argument_group('FFmpeg General Output Options')
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
        ffmpeg_group.add_argument('-fo', '--ffmpeg-options', dest='ffmpeg_options',
                help = 'Additional options for running FFmpeg',
                type = str,
                default = FFmpegCommands.CONVERT_COPY_VBR_QUALITY)

        misc_group = parser.add_argument_group('FFmpeg Commands Execution')
        #misc_group.add_argument("-pm", "--preserve-meta", dest='preserve_metadata',
        #            help = "Preserve metadata of processed files",
        #            action='store_true')
        misc_group.add_argument("-se", "--serial-exec", dest='serial_exec',
                    help = "Run all task's commands in a single process",
                    action='store_true')
        misc_group.add_argument("-q", "--quiet", dest = 'quiet',
                    help = "Do not display info messages during processing",
                    action = 'store_true')

        # Commands
        subparsers = parser.add_subparsers(dest='sub_cmd',
                                                title = 'BMFP Commands',
                                                    metavar = BMFPCommands.commands_meta())
        self._add_version(subparsers)
        self._add_info(subparsers)

        # Print
        print_parser = subparsers.add_parser(BMFPCommands.PRINT, description = 'Print source directory',
                                                                formatter_class = BatchMPHelpFormatter)
        print_parser.add_argument('-sl', '--startlevel', dest='start_level',
                help = 'Initial nested level for printing (0, i.e. root source directory by default)',
                type = int,
                default = 0)
        print_parser.add_argument('-ss', '--show-size', dest='show_size',
                help ='Shows files size',
                action = 'store_true')
        print_parser.add_argument('-st', '--show-tags', dest='show_tags',
                help ='Shows media tags',
                action = 'store_true')
        print_parser.add_argument('-sv', '--show-volume', dest='show_volume',
                help ='Shows volume statistics',
                action = 'store_true')
        print_parser.add_argument('-se', '--show-silence', dest='show_silence',
                help ='Shows silence',
                action = 'store_true')

        # Convert
        convert_parser = subparsers.add_parser(BMFPCommands.CONVERT,
                                                    description = 'Converts media to specified format',
                                                    formatter_class = BatchMPHelpFormatter)
        convert_parser.add_argument('-tf', '--target-format', dest='target_format',
                help = 'Target format file extension, e.g. mp3 / m4a / mp4 / mov /...',
                type = str,
                required = True)
        group = convert_parser.add_argument_group('Conversion Options')
        group.add_argument('-cc', '--change-container', dest='change_container',
                help = 'Changes media container without actual re-encoding of contained streams. When specified, ' \
                       'takes priority over all other option switches except for those explicitly specified via "-fo/ --ffmpeg-options"',
                action='store_true')
        group.add_argument('-la', '--lossless-audio', dest='lossless_audio',
                help = 'For media formats with support for lossless audio, tries a lossless conversion',
                action='store_true')

        # Nomalize
        norm_parser = subparsers.add_parser(BMFPCommands.NORMALIZE,
                                            description = 'Nomalizes media files. ' \
                                                          'Both Peak and RMS normalizations are supported, ' \
                                                          'Peak normalization is the default',
                                            formatter_class = BatchMPHelpFormatter)
        group = norm_parser.add_argument_group('RMS Normalization')
        group.add_argument('-rm', '--rms', dest='rms_norm',
                help ='(TBD) Leverages RMS-based normalization to set average loudness across selected media files',
                action = 'store_true')
        group.add_argument('-ac', '--allow-clipping', dest = 'allow_clipping',
                help ='(TBD) Allows clipping, via turning off automatic limiting of the gain applied (use with caution)',
                action = 'store_true')

        # Fragment
        fragment_parser = subparsers.add_parser(BMFPCommands.FRAGMENT,
                                            description = 'Extracts a fragment via specified start time & duration',
                                            formatter_class = BatchMPHelpFormatter)
        group = fragment_parser.add_argument_group('Fragment parameters')
        group.add_argument('-fs', '--starttime', dest='fragment_starttime',
                help = 'Fragment start time, in seconds or in the "hh:mm:ss[.xxx]" format',
                type = lambda f: self._is_timedelta(parser, f),
                required = True)
        group.add_argument('-fd', '--duration', dest='fragment_duration',
                help = 'Fragment duration, in seconds or in the "hh:mm:ss[.xxx]" format',
                type = lambda f: self._is_timedelta(parser, f),
                default = timedelta(days = 380))

        # Segment
        segment_parser = subparsers.add_parser(BMFPCommands.SEGMENT,
                                            description = 'Segments media by specified maximum duration or file size',
                                            formatter_class = BatchMPHelpFormatter)
        segment_group = segment_parser.add_mutually_exclusive_group()
        segment_group.add_argument('-fs', '--filesize', dest='segment_filesize',
                help = 'Maximum media file size in MB',
                type = float,
                default = 0.0)
        segment_group.add_argument('-sd', '--duration', dest='segment_duration',
                help = 'Maximum media duration, in seconds or in the "hh:mm:ss[.xxx]" format',
                type = lambda f: self._is_timedelta(parser, f),
                default = timedelta(0))
        segment_parser.add_argument("-rt", "--reset-timestamps", dest='reset_timestamps',
                    help = "Reset timestamps at the begin of each segment, so that it "
                            "starts with near-zero timestamps and therefore there are minimum pauses "
                            "betweeen segments when played one after another. "
                            "May not work well for some formats / combinations of muxers/codecs",
                    action='store_true')

        # Silence Split
        silencesplit_parser = subparsers.add_parser(BMFPCommands.SILENCESPLIT,
                                                description = 'Splits media files into segments via detecting specified silence',
                                                formatter_class = BatchMPHelpFormatter)
        silencesplit_group = silencesplit_parser.add_argument_group('Silence detection parameters')
        silencesplit_group.add_argument('-md', '--min-duration', dest='min_duration',
                help = 'Minimal silence duration, in seconds or in the "hh:mm:ss[.xxx]" format (default is {} seconds).' \
                                                .format(FFHDefaults.DEFAULT_SILENCE_MIN_DURATION),
                type = lambda md: self._is_timedelta(parser, md),
                default = timedelta(seconds = FFHDefaults.DEFAULT_SILENCE_MIN_DURATION))
        silencesplit_group.add_argument('-nt', '--noise-tolerance', dest='noise_tolerance',
                help = 'Silence noise tolerance, specified as amplitude ratio (default is {})' \
                                                .format(FFHDefaults.DEFAULT_SILENCE_NOISE_TOLERANCE),
                type = float,
                default = FFHDefaults.DEFAULT_SILENCE_NOISE_TOLERANCE)
        silencesplit_group.add_argument('-ad', '--auto-duration', dest='auto_duration',
                help = 'Automatically selects representative silence duration',
                action='store_true')        
        silencesplit_group.add_argument('-td', '--trim-duration', dest='trimmed_duration',
                help = 'Trims target silence start durations to a given value, in seconds or in the "hh:mm:ss[.xxx]" format (default is {} seconds).' \
                                                .format(FFHDefaults.DEFAULT_SILENCE_TARGET_TRIMMED_DURATION),
                type = lambda md: self._is_timedelta(parser, md),
                default = timedelta(seconds = FFHDefaults.DEFAULT_SILENCE_TARGET_TRIMMED_DURATION))

        silencesplit_parser.add_argument("-rt", "--reset-timestamps", dest='reset_timestamps',
                    help = "Reset timestamps at the begin of each segment, so that it "
                            "starts with near-zero timestamps and therefore there are minimum pauses "
                            "betweeen segments when played one after another. "
                            "May not work well for some formats / combinations of muxers/codecs",
                    action='store_true')

        # Cue Split
        cuesplit_parser = subparsers.add_parser(BMFPCommands.CUESPLIT,
                                                description = 'Splits media files according to their respective cue sheets',
                                                formatter_class = BatchMPHelpFormatter)

        cuesplit_parser.add_argument('-en', '--encoding', dest='encoding',
                help = 'Cue file encoding, utf-8 by default',
                type = str,
                default = 'utf-8')

        group = cuesplit_parser.add_argument_group('Conversion Options')
        group.add_argument('-tf', '--target-format', dest='target_format',
                help = 'Target format file extension, e.g. mp3 / m4a / mp4 ...',
                type = str,
                required = True)
        group.add_argument('-la', '--lossless-audio', dest='lossless_audio',
                help = 'For media formats with support for lossless audio, tries a lossless conversion',
                action='store_true')


        # Denoise
        denoise_parser = subparsers.add_parser(BMFPCommands.DENOISE,
                                        description = 'Reduces background audio noise in media files via filtering out highpass / low-pass frequencies',
                                        formatter_class = BatchMPHelpFormatter)
        denoise_parser.add_argument('-np', '--numpasses', dest='num_passes',
                help = 'Applies filters in multiple passes',
                type = int,
                default = Denoiser.DEFAULT_NUM_PASSES)
        group = denoise_parser.add_argument_group('Pass Filters')
        group.add_argument("-hp", "--highpass", dest='highpass',
                    help = "Cutoff boundary for lower frequencies",
                    type = int,
                    default = Denoiser.DEFAULT_HIGHPASS)
        group.add_argument("-lp", "--lowpass", dest='lowpass',
                    help = "Cutoff boundary for higher frequencies",
                    type = int,
                    default = Denoiser.DEFAULT_LOWPASS)

        # Troubleshooting
        parser.add_argument('-.ll', dest='log_level',
            help=argparse.SUPPRESS,
            type = int,
            choices = [LogLevel.QUIET, LogLevel.FFMPEG, LogLevel.VERBOSE],
            default = LogLevel.QUIET)

    # Args Checking
    def default_command(self, args, parser):
        args['sub_cmd'] = BMFPCommands.PRINT
        args['start_level'] = 0
        args['show_size'] = False
        args['show_tags'] = False
        args['show_volume'] = False
        args['show_silence'] = False

    def check_args(self, args, parser):
        ''' Validation of supplied BMFP CLI arguments
        '''
        # Global options check
        super().check_args(args, parser)

        # if input source is a file, adjust the target directory
        if args['file']:
            if not args['target_dir']:
                args['target_dir'] = os.path.dirname(args['file'])

        # only consider playable media files by default
        if args['file_type'] == FSEntryDefaults.DEFAULT_FILE_TYPE and args['sub_cmd'] != BMFPCommands.CUESPLIT:
            args['file_type'] = FSEntryDefaults.DEFAULT_MEDIA_TYPE

        # Compile FF global options
        ff_general_options = 0
        if args['all_streams']:
            ff_general_options |= FFmpegBitMaskOptions.MAP_ALL_STREAMS
        if args['copy_codecs']:
            ff_general_options |= FFmpegBitMaskOptions.COPY_CODECS
        if args['exclude_video']:
            ff_general_options |= FFmpegBitMaskOptions.DISABLE_VIDEO
        if args['exclude_audio']:
            ff_general_options |= FFmpegBitMaskOptions.DISABLE_AUDIO
        if args['exclude_subtitles']:
            ff_general_options |= FFmpegBitMaskOptions.DISABLE_SUBTITLES

        args['ff_general_options'] = ff_general_options

        # Always preserve metadata (experimental)
        args['preserve_metadata'] = True

        # If advanced media options requested,
        # check ffmpeg presence
        if args['sub_cmd'] == 'print':
            if args['show_volume'] or args['show_silence']:
                if not FFH.ffmpeg_installed():
                    print('Advanced media content operations require FFmpeg')
                    print(FFmpegNotInstalled().default_message)
                    sys.exit(0)

        # Segment attributes check
        elif args['sub_cmd'] == BMFPCommands.SEGMENT:
            if not args['segment_filesize'] and not args['segment_duration'].total_seconds():
                parser.error('bmfp segment:\n\t'
                             'One of the command parameters needs to be specified: <filesize | duration>')

        elif args['sub_cmd'] in (BMFPCommands.CONVERT, BMFPCommands.CUESPLIT):
            # Convert attributes check
            args['target_format'] = args['target_format'].lower()
            if not args['target_format'].startswith('.'):
                args['target_format'] = '.{}'.format(args['target_format'])

            if args['ffmpeg_options'] == FFmpegCommands.CONVERT_COPY_VBR_QUALITY: #default
                if args['lossless_audio']:
                    # takes priority over default settings
                    args['ffmpeg_options'] = FFmpegCommands.CONVERT_LOSSLESS

                if args['sub_cmd'] == BMFPCommands.CONVERT and args['change_container']:
                    # takes priority over default settings or lossless
                    args['ffmpeg_options'] = FFmpegCommands.CONVERT_CHANGE_CONTAINER

        if not args['ffmpeg_options'].startswith(' '):
            # add a space if needed
            args['ffmpeg_options'] = ' {}'.format(args['ffmpeg_options'])


    # Internal Helpers
    @staticmethod
    def _add_arg_misc_group(parser):
        pass




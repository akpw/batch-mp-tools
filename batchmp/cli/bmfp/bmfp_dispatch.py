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

from batchmp.cli.base.bmp_dispatch import BatchMPDispatcher
from batchmp.cli.bmfp.bmfp_options import BMFPArgParser, BMFPCommands
from batchmp.ffmptools.ffcommands.convert import Convertor
from batchmp.ffmptools.ffcommands.segment import Segmenter
from batchmp.ffmptools.ffcommands.fragment import Fragmenter
from batchmp.ffmptools.ffcommands.silencesplit import SilenceSplitter
from batchmp.ffmptools.ffcommands.denoise import Denoiser
from batchmp.ffmptools.ffcommands.normalize_peak import PeakNormalizer
from batchmp.ffmptools.ffcommands.cuesplit import CueSplitter
from batchmp.ffmptools.processors.basefp import BaseFFProcessor
from batchmp.tags.output.formatters import OutputFormatType


class BMFPDispatcher(BatchMPDispatcher):
    ''' BMFP commands Dispatcher
    '''
    def __init__(self):
        self.option_parser = BMFPArgParser()

    # Dispatcher
    def dispatch(self):
        ''' Dispatches BMFP commands
        '''
        if not super().dispatch():
            args = self.option_parser.parse_options()
            if args['sub_cmd'] == BMFPCommands.PRINT:
                self.print_dir(args)

            elif args['sub_cmd'] == BMFPCommands.CONVERT:
                self.convert(args)

            elif args['sub_cmd'] == BMFPCommands.DENOISE:
                self.denoise(args)

            elif args['sub_cmd'] == BMFPCommands.NORMALIZE:
                self.normalize(args)

            elif args['sub_cmd'] == BMFPCommands.FRAGMENT:
                self.fragment(args)

            elif args['sub_cmd'] == BMFPCommands.SEGMENT:
                self.segment(args)

            elif args['sub_cmd'] == BMFPCommands.SILENCESPLIT:
                self.silence_split(args)

            elif args['sub_cmd'] == BMFPCommands.CUESPLIT:
                self.cue_split(args)

            else:
                print('Nothing to dispatch')
                return False

        return True

    # Dispatched Methods
    def print_dir(self, args):
        BaseFFProcessor().print_dir(src_dir = args['dir'],
                start_level = args['start_level'], end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                show_size = args['show_size'], show_stats = True,
                format = OutputFormatType.STATS if not args['show_tags'] else OutputFormatType.FULL,
                show_volume = args['show_volume'], show_silence = args['show_silence'])

    def convert(self, args):
        Convertor().convert(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                serial_exec = args['serial_exec'],
                target_dir = args['target_dir'], log_level = args['log_level'],
                target_format = args['target_format'],
                ff_general_options = args['ff_general_options'], ff_other_options = args['ffmpeg_options'],
                preserve_metadata = args['preserve_metadata'])

    def denoise(self, args):
        Denoiser().apply_af_filters(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                target_dir = args['target_dir'], log_level = args['log_level'],
                num_passes=args['num_passes'], highpass=args['highpass'], lowpass=args['lowpass'],
                ff_general_options = args['ff_general_options'], ff_other_options = args['ffmpeg_options'],
                preserve_metadata = args['preserve_metadata'])

    def normalize(self, args):
        PeakNormalizer().peak_normalize(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                target_dir = args['target_dir'], log_level = args['log_level'],
                ff_general_options = args['ff_general_options'], ff_other_options = args['ffmpeg_options'],
                preserve_metadata = args['preserve_metadata'])

    def fragment(self, args):
        Fragmenter().fragment(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                target_dir = args['target_dir'], log_level = args['log_level'],
                fragment_starttime = args['fragment_starttime'].total_seconds(),
                fragment_duration = args['fragment_duration'].total_seconds(),
                serial_exec = args['serial_exec'],
                ff_general_options = args['ff_general_options'], ff_other_options = args['ffmpeg_options'],
                preserve_metadata = args['preserve_metadata'])

    def segment(self, args):
        Segmenter().segment(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                target_dir = args['target_dir'], log_level = args['log_level'],
                segment_size_MB = args['segment_filesize'],
                segment_length_secs = args['segment_duration'].total_seconds(),
                serial_exec = args['serial_exec'],
                ff_general_options = args['ff_general_options'], ff_other_options = args['ffmpeg_options'],
                reset_timestamps = args['reset_timestamps'],
                preserve_metadata = args['preserve_metadata'])

    def silence_split(self, args):
        SilenceSplitter().silence_split(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                target_dir = args['target_dir'], log_level = args['log_level'],
                serial_exec = args['serial_exec'],
                ff_general_options = args['ff_general_options'], ff_other_options = args['ffmpeg_options'],
                preserve_metadata = args['preserve_metadata'],
                reset_timestamps = args['reset_timestamps'],
                silence_min_duration = args['min_duraiton'].total_seconds(),
                silence_noise_tolerance_amplitude_ratio = args['noise_tolerance'])

    def cue_split(self, args):
        CueSplitter().cue_split(src_dir = args['dir'],
                end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                serial_exec = args['serial_exec'],
                target_dir = args['target_dir'], log_level = args['log_level'],
                target_format = args['target_format'],
                ff_general_options = args['ff_general_options'], ff_other_options = args['ffmpeg_options'],
                preserve_metadata = args['preserve_metadata'],
                encoding = args['encoding'])


def main():
    ''' BMFP entry point
    '''
    BMFPDispatcher().dispatch()

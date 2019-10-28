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
from batchmp.ffmptools.processors.ffentry import FFEntryParams, FFEntryParamsExt, FFEntryParamsSilenceSplit

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
        ff_entry_params = FFEntryParams(args)
        BaseFFProcessor().print_dir(ff_entry_params,
                show_stats = True,
                format = OutputFormatType.STATS if not args['show_tags'] else OutputFormatType.FULL,
                show_volume = args['show_volume'], show_silence = args['show_silence'])

    def convert(self, args):
        ff_entry_params = FFEntryParamsExt(args)
        Convertor().convert(ff_entry_params)

    def denoise(self, args):
        ff_entry_params = FFEntryParamsExt(args)
        Denoiser().apply_af_filters(ff_entry_params,
                num_passes=args['num_passes'], 
                highpass=args['highpass'], 
                lowpass=args['lowpass'])

    def normalize(self, args):
        ff_entry_params = FFEntryParamsExt(args)
        PeakNormalizer().peak_normalize(ff_entry_params)

    def fragment(self, args):
        ff_entry_params = FFEntryParamsExt(args)
        Fragmenter().fragment(ff_entry_params,
                fragment_starttime = args['fragment_starttime'].total_seconds(),
                fragment_duration = args['fragment_duration'].total_seconds())

    def segment(self, args):
        ff_entry_params = FFEntryParamsExt(args)
        Segmenter().segment(ff_entry_params,
                segment_size_MB = args['segment_filesize'],
                segment_length_secs = args['segment_duration'].total_seconds(),
                reset_timestamps = args['reset_timestamps'])

    def silence_split(self, args):
        ff_entry_params = FFEntryParamsSilenceSplit(args)
        SilenceSplitter().silence_split(ff_entry_params)               

    def cue_split(self, args):
        ff_entry_params = FFEntryParamsExt(args)
        CueSplitter().cue_split(ff_entry_params, encoding = args['encoding'])


def main():
    ''' BMFP entry point
    '''
    BMFPDispatcher().dispatch()

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


import sys, math, datetime
from batchmp.commons.utils import MiscHelpers
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.builders.fsentry import FSEntry, FSEntryType
from batchmp.ffmptools.ffutils import FFH, FFmpegNotInstalled
from batchmp.tags.output.formatters import TagOutputFormatter, OutputFormatType
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from functools import partial


class BaseFFProcessor:
    ''' Base Tag Processing
    '''
    def __init__(self):
        self._handler = MutagenTagHandler() + FFmpegTagHandler()

    @property
    def handler(self):
        return self._handler

    def print_dir(self, ff_entry_params,
                            show_size = False, format = None, show_stats = False,
                            show_volume = False, show_silence = False):

        ''' Prints tags in selected media files
        '''

        if show_volume or show_silence:
            if not FFH.ffmpeg_installed():
                print(FFmpegNotInstalled().default_message)
                sys.exit(0)

        base_formatter = partial(TagOutputFormatter.tags_formatter,
                                        format = format if format else OutputFormatType.COMPACT,
                                        handler = self.handler,
                                        show_stats = show_stats)

        def volume_formatter(entry):
            volume_str = ''
            if show_volume:
                if entry.type == FSEntryType.FILE:
                    if self.handler.can_handle(entry.realpath):
                        volume_entry = FFH.volume_detector(entry.realpath)
                        indent = entry.indent[:-3] + TagOutputFormatter.DEFAULT_TAG_INDENT
                        if not volume_entry:
                            volume_str = '\n{}No volume detected'.format(indent)
                        else:
                            volume_str = '\n{0}{1}: -{2}dB, {3}: -{4}dB'.format(indent,
                                                    'Max Volume', volume_entry.max_volume,
                                                    'Mean Volume', volume_entry.mean_volume)
            return volume_str

        def silence_formatter(entry):
            silence_str = ''
            if show_silence:
                if entry.type == FSEntryType.FILE:
                    if self.handler.can_handle(entry.realpath):
                        indent = entry.indent[:-3] + TagOutputFormatter.DEFAULT_TAG_INDENT
                        silence_entries = FFH.silence_detector(entry.realpath)
                        if not silence_entries:
                            silence_str = '\n{}No silence detected'.format(indent)
                        else:
                            silence_str = '\n{}Detected Silences:'.format(indent)
                            indent = '{}  '.format(indent)
                            for silence_entry in silence_entries:
                                silence_str = '{0}\n{1}{2}: {3}, {4}: {5}, {6}: {7}'.format(
                                    silence_str, indent,
                                    'Start', MiscHelpers.time_delta_str(silence_entry.silence_start),
                                    'End', MiscHelpers.time_delta_str(silence_entry.silence_end),
                                    'Duration', MiscHelpers.time_delta_str(silence_entry.silence_end - silence_entry.silence_start))
            return silence_str


        DHandler.print_dir(ff_entry_params,
                            formatter = [base_formatter, volume_formatter, silence_formatter],
                            selected_files_description = 'media file')


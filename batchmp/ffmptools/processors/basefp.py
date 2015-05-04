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
from batchmp.fstools.fsutils import DWalker
from batchmp.ffmptools.ffutils import FFH
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

    def print_dir(self, src_dir, *,
                            start_level = 0, end_level = sys.maxsize,
                            include = None, exclude = None,
                            sort = None, nested_indent = DWalker.DEFAULT_NESTED_INDENT,
                            filter_dirs = True, filter_files = True,
                            show_size = False, format = None, show_stats = False,
                            show_volume = False, show_silence = False):

        ''' Prints tags in selected media files
        '''
        base_formatter = partial(TagOutputFormatter.tags_formatter,
                                        format = format if format else OutputFormatType.COMPACT,
                                        handler = self.handler,
                                        show_stats = show_stats)

        def volume_formatter(entry):
            volume_str = ''
            if show_volume:
                if entry.type == DWalker.ENTRY_TYPE_FILE:
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
                if entry.type == DWalker.ENTRY_TYPE_FILE:
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


        DHandler.print_dir(src_dir = src_dir,
                            start_level = start_level, end_level = end_level,
                            include = include, exclude = exclude,
                            sort = sort, nested_indent = nested_indent,
                            filter_dirs = filter_dirs, filter_files = filter_files,
                            show_size = show_size,
                            formatter = [base_formatter, volume_formatter, silence_formatter],
                            selected_files_description = 'media file')


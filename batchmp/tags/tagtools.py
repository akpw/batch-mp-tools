# coding=utf8
## Copyright (c) 2014 Arseniy Kuznetsov
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

import sys, os, datetime, math
from batchmp.fstools.dirtools import DHandler
from batchmp.tags.handlers import MutagenTagHandler, FFmpegTagHandler

class THandler:
    def __init__(self):
        mHandler = MutagenTagHandler()
        ffHandler = FFmpegTagHandler()
        self._handlers = [mHandler, ffHandler]

    def media_handler(self, mfname):
        for handler in self._handlers:
            if handler.can_handle(mfname):
                return handler
        return None

    def print_dir(self, src_dir, start_level = 0, end_level = sys.maxsize,
                            include = '*', exclude = '', sort = 'n',
                            filter_dirs = True, filter_files = True,
                            flatten = False, ensure_uniq = False,
                            show_size = False, formatter = None):

        # Formatter
        def tag_formatter(entry):
            handler = self.media_handler(entry.realpath)
            if not handler:
                return entry.basename
            else:
                indent = entry.indent[:-3] + '\t'
                media_str = ''
                if handler.title:
                    media_str = '\n{0}Title: {1}'.format(indent, handler.title)
                if handler.album:
                    media_str = '{0}\n{1}Album: {2}'.format(media_str, indent, handler.album)

                if handler.albumartist:
                    media_str = '{0}\n{1}Artist: {2}'.format(media_str, indent, handler.albumartist)
                elif handler.artist:
                    media_str = '{0}\n{1}Artist: {2}'.format(media_str, indent, handler.artist)

                if handler.genre:
                    media_str = '{0}\n{1}Genre: {2}'.format(media_str, indent, handler.genre)
                if handler.composer:
                    media_str = '{0}\n{1}Composer: {2}'.format(media_str, indent, handler.composer)

                if handler.track:
                    if handler.tracktotal:
                        track = '{}/{}'.format(handler.track, handler.tracktotal)
                    else:
                        track = handler.track
                    media_str = '{0}\n{1}Track Number: {2}'.format(media_str, indent, track)

                if handler.has_artwork:
                    media_str = '{0}\n{1}Artwork present'.format(media_str, indent)

                duration = datetime.timedelta(seconds = math.ceil(handler.length)) if handler.length else 0
                bitrate = math.ceil(handler.bitrate / 1000) if handler.bitrate else 0
                samplerate = handler.samplerate if handler.samplerate else 0
                media_str = '{0}\n{1}Duration: {2}, Bit rate: {3}kb/s, Sampling: {4}Hz'.format(media_str, indent,
                                                           duration, bitrate, samplerate)

                return '{0}{1}'.format(entry.basename, media_str)

        if not formatter:
            formatter = tag_formatter

        DHandler.print_dir(src_dir, start_level = 0, end_level = end_level,
                            include = include, exclude = exclude, sort = sort,
                            filter_dirs = filter_dirs, filter_files = filter_files,
                            flatten = flatten, ensure_uniq = ensure_uniq,
                            show_size = show_size, formatter = formatter)





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

import datetime, math
from batchmp.fstools.fsutils import DWalker
from enum import Enum

class TagOutputFormatter(Enum):
    COMPACT = 0
    FULL = 1

    @staticmethod
    def tags_formatter(entry, *,
                       format_type = None, handler_factory = None, show_stats = True, tag_holder = None):
        if not format_type:
            format_type = TagOutputFormatter.COMPACT

        if entry.type == DWalker.ENTRY_TYPE_DIR or entry.type == DWalker.ENTRY_TYPE_ROOT:
            return entry.basename

        # check inputs
        if handler_factory:
            handler = handler_factory.handler(entry.realpath)
            if not handler:
                return None
        else:
            return None

        if tag_holder:
            handler.copy_fields(tag_holder, copy_empty_vals = False)

        # dispatch call to requested formatter
        if format_type == TagOutputFormatter.COMPACT:
            return TagOutputFormatter._compact_formatter(entry, handler, show_stats)
        elif format_type == TagOutputFormatter.FULL:
            return TagOutputFormatter._full_formatter(entry, handler, show_stats)
        else:
            return None

    @staticmethod
    def _compact_formatter(entry, handler, show_stats):
        indent = entry.indent[:-3] + '\t'
        media_str = ''
        if handler.title:
            media_str = '\n{0}Title: {1}'.format(indent, handler.title)
        if handler.album:
            media_str = '{0}\n{1}Album: {2}'.format(media_str, indent, handler.album)
        if handler.artist:
            media_str = '{0}\n{1}Artist: {2}'.format(media_str, indent, handler.artist)
        if handler.albumartist:
            media_str = '{0}\n{1}Album Artist: {2}'.format(media_str, indent, handler.albumartist)
        if handler.genre:
            media_str = '{0}\n{1}Genre: {2}'.format(media_str, indent, handler.genre)
        if handler.composer:
            media_str = '{0}\n{1}Composer: {2}'.format(media_str, indent, handler.composer)

        if handler.track:
            if handler.tracktotal:
                track = '{}/{}'.format(handler.track, handler.tracktotal)
            else:
                track = handler.track
            media_str = '{0}\n{1}Track: {2}'.format(media_str, indent, track)

        if handler.disc:
            if handler.disctotal:
                disc = '{}/{}'.format(handler.disc, handler.disctotal)
            else:
                disc = handler.disc
            media_str = '{0}\n{1}Disc: {2}'.format(media_str, indent, disc)

        if show_stats:
            if handler.has_artwork:
                media_str = '{0}\n{1}Artwork present'.format(media_str, indent)

            duration = datetime.timedelta(seconds = math.ceil(handler.length)) if handler.length else None
            duration = 'Duration: {}'.format(duration if duration else 'n/a')

            bitrate = math.ceil(handler.bitrate / 1000) if handler.bitrate else None
            bitrate = 'Bit rate: {}'.format('{}kb/s'.format(bitrate) if bitrate else 'n/a')

            samplerate = handler.samplerate if handler.samplerate else None
            samplerate = 'Sampling: {}'.format('{}Hz'.format(samplerate) if samplerate else 'n/a')

            bitdepth = handler.bitdepth if handler.bitdepth else None
            bitdepth = 'Bit depth: {}'.format(bitdepth if bitdepth else 'n/a')

            media_str = '{0}\n{1}{2}, {3}, {4}, {5}'.format(media_str, indent, duration, bitrate, samplerate, bitdepth)

        return '{0}{1}'.format(entry.basename, media_str)


    @staticmethod
    def _full_formatter(entry, handler, show_stats):
        indent = entry.indent[:-3] + '\t'
        media_str = ''
        filter = ('art', 'images', 'length', 'samplerate', 'bitdepth', 'disc', 'disctotal', 'track', 'tracktotal')
        for field in sorted(handler.fields()):
            if not (field in filter):
                field_val = getattr(handler, field)
            else:field_val = None
            if field_val:
                media_str = '{0}\n{1}{2}: {3}'.format(media_str, indent, field.title(), field_val)

        if handler.track:
            if handler.tracktotal:
                track = '{}/{}'.format(handler.track, handler.tracktotal)
            else:
                track = handler.track
            media_str = '{0}\n{1}Track: {2}'.format(media_str, indent, track)

        if handler.disc:
            if handler.disctotal:
                disc = '{}/{}'.format(handler.disc, handler.disctotal)
            else:
                disc = handler.disc
            media_str = '{0}\n{1}Disc: {2}'.format(media_str, indent, disc)

        if show_stats:
            if handler.has_artwork:
                media_str = '{0}\n{1}Artwork present'.format(media_str, indent)

            duration = datetime.timedelta(seconds = math.ceil(handler.length)) if handler.length else None
            duration = 'Duration: {}'.format(duration if duration else 'n/a')

            bitrate = math.ceil(handler.bitrate / 1000) if handler.bitrate else None
            bitrate = 'Bit rate: {}'.format('{}kb/s'.format(bitrate) if bitrate else 'n/a')

            samplerate = handler.samplerate if handler.samplerate else None
            samplerate = 'Sampling: {}'.format('{}Hz'.format(samplerate) if samplerate else 'n/a')

            bitdepth = handler.bitdepth if handler.bitdepth else None
            bitdepth = 'Bit depth: {}'.format(bitdepth if bitdepth else 'n/a')

            media_str = '{0}\n{1}{2}, {3}, {4}, {5}'.format(media_str, indent, duration, bitrate, samplerate, bitdepth)

        return '{0}{1}'.format(entry.basename, media_str)

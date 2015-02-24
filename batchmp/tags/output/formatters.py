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


class OutputFormatType(Enum):
    COMPACT = 0
    FULL = 1
    TRACKS = 2

class TagOutputFormatter:
    @staticmethod
    def tags_formatter(entry, *,
                       format = None, handler = None, show_stats = True,
                       tag_holder = None, tag_holder_gen = None, copy_empty_vals = False):

        # check inputs
        if entry.type == DWalker.ENTRY_TYPE_DIR or entry.type == DWalker.ENTRY_TYPE_ROOT:
            return entry.basename

        if not handler or not handler.can_handle(entry.realpath):
            return None

        if not format or (format not in OutputFormatType):
            format = OutputFormatType.COMPACT

        if tag_holder_gen:
            try:
                th = next(tag_holder_gen)
            except StopIteration as e:
                pass
            else:
                tag_holder = th

        if tag_holder:
            handler.tag_holder.copy_tags(tag_holder, copy_empty_vals = copy_empty_vals)

        # dispatch call to requested formatter
        if format == OutputFormatType.COMPACT:
            return TagOutputFormatter._compact_formatter(entry, handler, show_stats)
        elif format == OutputFormatType.FULL:
            return TagOutputFormatter._full_formatter(entry, handler, show_stats)
        elif format == OutputFormatType.TRACKS:
            return TagOutputFormatter._tracks_formatter(entry, handler)
        else:
            return None

    # Formatter methods
    @staticmethod
    def _compact_formatter(entry, handler, show_stats):
        indent = entry.indent[:-3] + '\t'
        media_str = ''
        if handler.tag_holder.title:
            media_str = '\n{0}Title: {1}'.format(indent, handler.tag_holder.title)
        if handler.tag_holder.album:
            media_str = '{0}\n{1}Album: {2}'.format(media_str, indent, handler.tag_holder.album)
        if handler.tag_holder.artist:
            media_str = '{0}\n{1}Artist: {2}'.format(media_str, indent, handler.tag_holder.artist)
        if handler.tag_holder.albumartist:
            media_str = '{0}\n{1}Album Artist: {2}'.format(media_str, indent, handler.tag_holder.albumartist)
        if handler.tag_holder.genre:
            media_str = '{0}\n{1}Genre: {2}'.format(media_str, indent, handler.tag_holder.genre)
        if handler.tag_holder.composer:
            media_str = '{0}\n{1}Composer: {2}'.format(media_str, indent, handler.tag_holder.composer)
        if handler.tag_holder.year:
            media_str = '{0}\n{1}Year: {2}'.format(media_str, indent, handler.tag_holder.year)

        if handler.tag_holder.track:
            media_str = TagOutputFormatter._track_str(handler, indent, media_str)
        if handler.tag_holder.disc:
            media_str = TagOutputFormatter._disc_str(handler, indent, media_str)

        if show_stats:
            media_str = TagOutputFormatter._stats_str(handler, indent, media_str)

        return '{0}{1}'.format(entry.basename, media_str)

    @staticmethod
    def _full_formatter(entry, handler, show_stats):
        indent = entry.indent[:-3] + '\t'
        media_str = TagOutputFormatter._compact_formatter(entry, handler, show_stats = False)

        filter = ('title', 'album', 'artist', 'albumartist', 'genre', 'composer', 'year',
                                'art', 'images', 'disc', 'disctotal', 'track', 'tracktotal')
        fields = (f for f in sorted(handler.tag_holder.taggable_fields()) if not f in filter)
        for field in fields:
            field_val = getattr(handler.tag_holder, field)
            if field_val:
                media_str = '{0}\n{1}{2}: {3}'.format(media_str, indent, field.title(), field_val)

        if show_stats:
            media_str = TagOutputFormatter._stats_str(handler, indent, media_str)

        return media_str

    @staticmethod
    def _tracks_formatter(entry, handler):
        indent = entry.indent[:-3] + '\t'
        media_str = ''
        if handler.tag_holder.track:
            media_str = TagOutputFormatter._track_str(handler, indent, media_str)
        return '{0}{1}'.format(entry.basename, media_str)

    # Helpers
    @staticmethod
    def _disc_str(handler, indent, media_str):
        if handler.tag_holder.disctotal:
            disc_str = '{}/{}'.format(handler.tag_holder.disc, handler.tag_holder.disctotal)
        else:
            disc_str = handler.tag_holder.disc
        return '{0}\n{1}Disk: {2}'.format(media_str, indent, disc_str)

    @staticmethod
    def _track_str(handler, indent, media_str, show_always = False):
        if handler.tag_holder.tracktotal:
            track_str = '{}/{}'.format(handler.tag_holder.track, handler.tag_holder.tracktotal)
        else:
            track_str = handler.tag_holder.track
        return '{0}\n{1}Track: {2}'.format(media_str, indent, track_str)

    @staticmethod
    def _stats_str(handler, indent, media_str):
        if handler.tag_holder.format:
            media_str = '{0}\n{1}Format: {2}'.format(media_str, indent, handler.tag_holder.format)

        if handler.tag_holder.has_artwork:
            media_str = '{0}\n{1}Artwork present'.format(media_str, indent)

        duration = datetime.timedelta(seconds = math.ceil(handler.tag_holder.length)) if handler.tag_holder.length else None
        duration = 'Duration: {}'.format(duration if duration else 'n/a')

        bitrate = math.ceil(handler.tag_holder.bitrate / 1000) if handler.tag_holder.bitrate else None
        bitrate = 'Bit rate: {}'.format('{}kb/s'.format(bitrate) if bitrate else 'n/a')

        samplerate = handler.tag_holder.samplerate if handler.tag_holder.samplerate else None
        samplerate = 'Sampling: {}'.format('{}Hz'.format(samplerate) if samplerate else 'n/a')

        bitdepth = handler.tag_holder.bitdepth if handler.tag_holder.bitdepth else None
        bitdepth = 'Bit depth: {}'.format(bitdepth if bitdepth else 'n/a')

        return '{0}\n{1}{2}, {3}, {4}, {5}'.format(media_str, indent, duration,
                                                                bitrate, samplerate, bitdepth)




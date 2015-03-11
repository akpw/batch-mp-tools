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
    DIFF = 2


class TagOutputFormatter:
    ''' Generates output for printing tags
    '''
    COMPACT_FIELDS = ['title', 'album', 'artist', 'albumartist', 'genre', 'composer', 'year']
    EXTENDED_FIELDS = ['encoder', 'bpm', 'comp', 'grouping', 'comments', 'lyrics']

    @staticmethod
    def tags_formatter(entry, *,
                       format = None, handler = None, show_stats = True,
                       tag_holder = None, tag_holder_gen = None, diff_fields = None,
                       copy_empty_vals = False):

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
            return TagOutputFormatter._formatter(entry, handler, show_stats = show_stats)
        elif format == OutputFormatType.FULL:
            return TagOutputFormatter._formatter(entry, handler,
                                                      show_extended = True, show_stats = show_stats)
        elif format == OutputFormatType.DIFF:
            return TagOutputFormatter._diff_formatter(entry, handler, diff_fields)
        else:
            return None

    # Formatter methods
    @staticmethod
    def _formatter(entry, handler, show_extended = False, show_stats = False):
        indent = entry.indent[:-3] + '\t'
        media_str = ''

        for field in TagOutputFormatter.COMPACT_FIELDS:
            field_val = getattr(handler.tag_holder, field)
            if field_val:
                media_str = '{0}\n{1}{2}: {3}'.format(media_str, indent,
                                                      TagOutputFormatter._tag_display_name(field),
                                                      field_val)
        # Tracks / Discs
        if handler.tag_holder.track or handler.tag_holder.tracktotal:
            media_str = TagOutputFormatter._track_str(handler, indent, media_str)
        if handler.tag_holder.disc or handler.tag_holder.disctotal:
            media_str = TagOutputFormatter._disc_str(handler, indent, media_str)

        if show_extended:
            for field in TagOutputFormatter.EXTENDED_FIELDS:
                field_val = getattr(handler.tag_holder, field)
                if field_val:
                    media_str = '{0}\n{1}{2}: {3}'.format(media_str, indent,
                                                          TagOutputFormatter._tag_display_name(field),
                                                          field_val)
            if handler.tag_holder.has_artwork:
                media_str = '{0}\n{1}Artwork present'.format(media_str, indent)

        # Stats
        if show_stats:
            media_str = TagOutputFormatter._stats_str(handler, indent, media_str)

        return '{0}{1}'.format(entry.basename, media_str)


    @staticmethod
    def _diff_formatter(entry, handler, diff_fields):
        indent = entry.indent[:-3] + '\t'
        media_str = ''
        track_set = disc_set = False
        for field in diff_fields:
            if field == 'art' and handler.tag_holder.has_artwork:
                media_str = '{0}\n{1}Artwork present'.format(media_str, indent)
            elif field in ('disc', 'disctotal'):
                if not disc_set:
                    disc_set = True
                    if handler.tag_holder.disc or handler.tag_holder.disctotal:
                        media_str = TagOutputFormatter._disc_str(handler, indent, media_str)
            elif field in ('track', 'tracktotal'):
                if not track_set:
                    track_set = True
                    if handler.tag_holder.track or handler.tag_holder.tracktotal:
                        media_str = TagOutputFormatter._track_str(handler, indent, media_str)
            else:
                field_val = getattr(handler.tag_holder, field)
                if field_val:
                    media_str = '{0}\n{1}{2}: {3}'.format(media_str, indent,
                                                          TagOutputFormatter._tag_display_name(field),
                                                          field_val)
        return '{0}{1}'.format(entry.basename, media_str)

    # Helpers
    @staticmethod
    def _disc_str(handler, indent, media_str):
        disc = handler.tag_holder.disc if handler.tag_holder.disc else '_'
        if handler.tag_holder.disctotal:
            disc_str = '{}/{}'.format(disc, handler.tag_holder.disctotal)
        else:
            disc_str = handler.tag_holder.disc
        return '{0}\n{1}Disk: {2}'.format(media_str, indent, disc_str)

    @staticmethod
    def _track_str(handler, indent, media_str, show_always = False):
        track = handler.tag_holder.track if handler.tag_holder.track else '_'
        if handler.tag_holder.tracktotal:
            track_str = '{}/{}'.format(track, handler.tag_holder.tracktotal)
        else:
            track_str = handler.tag_holder.track
        return '{0}\n{1}Track: {2}'.format(media_str, indent, track_str)

    @staticmethod
    def _stats_str(handler, indent, media_str):
        if handler.tag_holder.format:
            media_str = '{0}\n{1}Format: {2}'.format(media_str, indent, handler.tag_holder.format)

        duration = datetime.timedelta(seconds = math.ceil(handler.tag_holder.length)) if handler.tag_holder.length else None
        duration = 'Duration: {}'.format(duration if duration else 'n/a')

        bitrate = math.ceil(handler.tag_holder.bitrate / 1000) if handler.tag_holder.bitrate else None
        bitrate = 'Bit rate: {}'.format('{}kb/s'.format(bitrate) if bitrate else 'n/a')

        samplerate = handler.tag_holder.samplerate if handler.tag_holder.samplerate else None
        samplerate = 'Sample rate: {}'.format('{}Hz'.format(samplerate) if samplerate else 'n/a')

        bitdepth = handler.tag_holder.bitdepth if handler.tag_holder.bitdepth else None
        bitdepth = 'Bit depth: {}'.format(bitdepth if bitdepth else 'n/a')

        return '{0}\n{1}{2}, {3}, {4}, {5}'.format(media_str, indent, duration,
                                                                bitrate, samplerate, bitdepth)

    @staticmethod
    def _tag_display_name(field):
        if field == 'title':
            return 'Title'
        elif field == 'album':
            return 'Album'
        elif field == 'artist':
            return 'Artist'
        elif field == 'albumartist':
            return 'Album Artist'
        elif field == 'genre':
            return 'Genre'
        elif field == 'composer':
            return 'Composer'
        elif field == 'track':
            return 'Track'
        elif field == 'tracktotal':
            return 'Track Total'
        elif field == 'disc':
            return 'Disc'
        elif field == 'disctotal':
            return 'Disc Total'
        elif field == 'year':
            return 'Year'
        elif field == 'encoder':
            return 'Encoder'
        elif field == 'bpm':
            return 'BPM'
        elif field == 'comp':
            return 'Compilation'
        elif field == 'grouping':
            return 'Grouping'
        elif field == 'comments':
            return 'Comments'
        elif field == 'lyrics':
            return 'Lyrics'

        return None


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


import datetime, math
from batchmp.fstools.fsutils import DWalker
from enum import IntEnum


class OutputFormatType(IntEnum):
    COMPACT = 0
    FULL = 1
    STATS = 2


class TagOutputFormatter:
    ''' Generates output for printing tags
    '''
    DEFAULT_TAG_INDENT = '    '

    COMPACT_FIELDS = ['title', 'album', 'artist', 'albumartist', 'genre', 'composer', 'year', 'track', 'tracktotal', 'disc', 'disctotal']
    EXTENDED_FIELDS = ['encoder', 'bpm', 'comp', 'grouping', 'comments', 'lyrics', 'art']

    @staticmethod
    def tags_formatter(entry, *,
                           format = None, handler = None, show_stats = False,
                           tag_holder = None, tag_holder_builder = None,
                           show_tag_holder_values = False,
                           diff_tags_only = False):

        ''' Tag formatting entry point
        '''

        # check inputs
        if entry.type == DWalker.ENTRY_TYPE_DIR or entry.type == DWalker.ENTRY_TYPE_ROOT:
            return entry.basename
        if not handler or not handler.can_handle(entry.realpath):
            return None

        if tag_holder_builder:
            tag_holder = tag_holder_builder(entry)

        if not format or (format not in OutputFormatType):
            if tag_holder:
                format = OutputFormatType.FULL
            else:
                format = OutputFormatType.COMPACT

        diff_fields = None
        if tag_holder:
            # figure out relevant fields to show
            diff_fields = []
            for field in tag_holder.taggable_fields():
                value = getattr(tag_holder, field)
                if (value is not None) or \
                        (tag_holder.copy_empty_vals) or \
                        (tag_holder.nullable_fields and (field in tag_holder.nullable_fields)):
                    diff_fields.append(field)

            if not diff_tags_only:
                # if need to show the changes along with other tag fields,
                # return a minimal set of compact fields + all changed fields (including extended)
                diff_extended_fields = list(set(diff_fields).intersection(set(TagOutputFormatter.EXTENDED_FIELDS)))
                diff_fields = TagOutputFormatter.COMPACT_FIELDS + diff_extended_fields

        if tag_holder and show_tag_holder_values:
            # if care for new values, copy tags / process templates
            handler.tag_holder.copy_tags(tag_holder)

        if format == OutputFormatType.COMPACT:
            return TagOutputFormatter._formatter(entry, handler.tag_holder, show_stats = show_stats)
        elif format == OutputFormatType.FULL:
            return TagOutputFormatter._formatter(entry, handler.tag_holder, show_extended = True,
                                                 show_stats = show_stats, diff_fields = diff_fields)
        elif format == OutputFormatType.STATS:
            return TagOutputFormatter._formatter(entry, handler.tag_holder,
                                                    show_compact = False, show_stats = show_stats)
        else:
            return None

    # Helpers
    @staticmethod
    def _formatter(entry, tag_holder,
                    show_compact = True, show_extended = False, show_stats = False,
                    diff_fields = None):
        indent = entry.indent[:-3] + TagOutputFormatter.DEFAULT_TAG_INDENT
        media_str = ''

        if diff_fields is not None:
            compact_fields = [f for f in TagOutputFormatter.COMPACT_FIELDS if f in diff_fields]
            extended_fields = [f for f in TagOutputFormatter.EXTENDED_FIELDS if f in diff_fields]
        else:
            compact_fields = TagOutputFormatter.COMPACT_FIELDS
            extended_fields = TagOutputFormatter.EXTENDED_FIELDS

        if show_compact:
            track_set = disc_set = False
            for field in compact_fields:
                field_val = getattr(tag_holder, field)
                if field_val:
                    if field in ('disc', 'disctotal'):
                        if not disc_set:
                            disc_set = True
                            if tag_holder.disc or tag_holder.disctotal:
                                media_str = TagOutputFormatter._disc_str(tag_holder, indent, media_str)
                    elif field in ('track', 'tracktotal'):
                        if not track_set:
                            track_set = True
                            if tag_holder.track or tag_holder.tracktotal:
                                media_str = TagOutputFormatter._track_str(tag_holder, indent, media_str)
                    else:
                        media_str = '{0}\n{1}{2}: {3}'.format(media_str, indent,
                                                          TagOutputFormatter._tag_display_name(field),
                                                          field_val)
        if show_extended:
            for field in extended_fields:
                field_val = getattr(tag_holder, field)
                if field_val:
                    if field == 'art':
                        if tag_holder.has_artwork:
                            media_str = '{0}\n{1}Artwork present'.format(media_str, indent)
                    else:
                        media_str = '{0}\n{1}{2}: {3}'.format(media_str, indent,
                                                          TagOutputFormatter._tag_display_name(field),
                                                          field_val)
        # Stats
        if show_stats:
            media_str = TagOutputFormatter._stats_str(tag_holder, indent, media_str)

        return '{0}{1}'.format(entry.basename, media_str)

    @staticmethod
    def _disc_str(tag_holder, indent, media_str):
        disc = tag_holder.disc if tag_holder.disc else '_'
        if tag_holder.disctotal:
            disc_str = '{}/{}'.format(disc, tag_holder.disctotal)
        else:
            disc_str = tag_holder.disc
        return '{0}\n{1}Disk: {2}'.format(media_str, indent, disc_str)

    @staticmethod
    def _track_str(tag_holder, indent, media_str, show_always = False):
        track = tag_holder.track if tag_holder.track else '_'
        if tag_holder.tracktotal:
            track_str = '{}/{}'.format(track, tag_holder.tracktotal)
        else:
            track_str = tag_holder.track
        return '{0}\n{1}Track: {2}'.format(media_str, indent, track_str)

    @staticmethod
    def _stats_str(tag_holder, indent, media_str):
        if tag_holder.format:
            media_str = '{0}\n{1}Format: {2}'.format(media_str, indent, tag_holder.format)

        duration = datetime.timedelta(seconds = math.ceil(tag_holder.length)) if tag_holder.length else None
        duration = 'Duration: {}'.format(duration if duration else 'n/a')

        bitrate = math.ceil(tag_holder.bitrate / 1000) if tag_holder.bitrate else None
        bitrate = 'Bit rate: {}'.format('{}kb/s'.format(bitrate) if bitrate else 'n/a')

        samplerate = tag_holder.samplerate if tag_holder.samplerate else None
        samplerate = 'Sample rate: {}'.format('{}Hz'.format(samplerate) if samplerate else 'n/a')

        bitdepth = tag_holder.bitdepth if tag_holder.bitdepth else None
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

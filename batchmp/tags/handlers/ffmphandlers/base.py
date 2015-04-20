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


""" FFmpeg generic handler (no format-related specifics)
"""
import os, shlex
from batchmp.commons.chainedhandler import ChainedHandler
from batchmp.tags.handlers.tagsholder import TagHolder
from batchmp.commons.utils import temp_dir
from batchmp.commons.utils import (
    run_cmd,
    CmdProcessingError
)

class FFBaseFormatHandler(ChainedHandler):
    ARTWORK_WRITER_SUPPORTED_FORMATS = ['MP3']

    ''' Base FFmpeg tags parse
    '''
    def __init__(self, tag_holder):
        self.media_entry = None
        self.tag_holder = tag_holder

    def __add__(self, tag_handler):
        tag_handler.tag_holder = self.tag_holder
        return super().__add__(tag_handler)

    def _can_handle(self, media_entry):
        self.media_entry = media_entry
        return True

    @property
    def path(self):
        if self.media_entry:
            return self.media_entry.path
        else:
            return None

    @property
    def type(self):
        if self.media_entry and self.media_entry.format:
            format = self.media_entry.format.get('format_name')
            if format:
                format = format.split(',')[0]
                return format.upper()
        return None

    @property
    def artwork_writer_supported_format(self):
        return self.type in self.ARTWORK_WRITER_SUPPORTED_FORMATS

   # tag handler operations
    def parse(self):
        return self.responder._parse()

    def build_save_cmd(self, art_path = None):
        return self.responder._build_save_cmd(art_path = art_path)

   # tag handler ops impl
    def _parse(self):
        ''' parses tags from FFmpeg output
        '''
        self._parse_tags()
        self._parse_stats()
        self._parse_art()

    def _parse_tags(self):
        # Tags
        if self.media_entry.format:
            tag_info = self.media_entry.format.get('tags')
            if not tag_info:
                tag_info = self.media_entry.audio.get('tags')
            if tag_info:
                tag_info = {k.lower():v for k,v in tag_info.items()}

                self.tag_holder.title = tag_info.get('title')
                self.tag_holder.album = tag_info.get('album')
                self.tag_holder.artist = tag_info.get('artist')
                self.tag_holder.albumartist = tag_info.get('album_artist')
                self.tag_holder.genre = tag_info.get('genre')
                self.tag_holder.year = tag_info.get('date')
                self.tag_holder.composer = tag_info.get('composer')
                self.tag_holder.encoder = tag_info.get('encoded_by')

                self.tag_holder.bpm = tag_info.get('tbpm') or tag_info.get('bpm')
                self.tag_holder.comp = tag_info.get('compilation')
                self.tag_holder.grouping = tag_info.get('tit1')
                self.tag_holder.comments = tag_info.get('comment')
                self.tag_holder.lyrics = tag_info.get('lyrics')

                if 'track' in tag_info:
                    track_info = tag_info['track'].split('/')
                    if len(track_info) > 0:
                        self.tag_holder.track = track_info[0]
                        self.tag_holder.tracktotal = track_info[len(track_info) - 1]
                if 'disc' in tag_info:
                    disc_info = tag_info['disc'].split('/')
                    if len(disc_info) > 0:
                        self.tag_holder.disc = disc_info[0]
                        self.tag_holder.disctotal = disc_info[len(disc_info) - 1]

    def _parse_stats(self):
        # Non-taggable fields
        # non-tagable fields defaults
        self.tag_holder.length = 0.0
        self.tag_holder.bitrate = 0
        self.tag_holder.samplerate = 0
        self.tag_holder.channels = 0
        self.tag_holder.bitdepth = 0

        if self.media_entry.audio:
            self.tag_holder.length = float(self.media_entry.audio.get('duration', 0.0))
            self.tag_holder.bitrate = int(self.media_entry.audio.get('bit_rate', 0))
            self.tag_holder.samplerate = int(self.media_entry.audio.get('sample_rate', 0))
            self.tag_holder.bitdepth = int(self.media_entry.audio.get('bits_per_sample', 0))
            self.tag_holder.channels = int(self.media_entry.audio.get('channels', 0))

        if self.media_entry.format:
            if self.tag_holder.bitrate == 0:
                self.tag_holder.bitrate = int(self.media_entry.format.get('bit_rate', 0))

            format = self.media_entry.format.get('format_name')
            if format:
                format = format.upper()
            format_long = self.media_entry.format.get('format_long_name')
            if format_long:
                format = '{0}: {1}'.format(format, format_long)

            if format:
                self.tag_holder.format = format.upper()

            if not self.tag_holder.length:
                self.tag_holder.length = float(self.media_entry.format.get('duration', 0.0))

    def _parse_art(self):
        # Art
        if self.media_entry.artwork:
            self.tag_holder.deferred_art_method = self.artwork_reader

    def _build_save_cmd(self, art_path = None):
        ''' build save cmd string
        '''
        track_tagger = disc_tagger = ''
        if self.tag_holder.track:
            if self.tag_holder.tracktotal:
                track_tagger = ' -metadata track="{0}/{1}"'.format(self.tag_holder.track,
                                                                    self.tag_holder.tracktotal)
            else:
                track_tagger = ' -metadata track="{}"'.format(self.tag_holder.track)
        elif self.tag_holder.tracktotal:
                track_tagger = ' -metadata track="0/{}"'.format(self.tag_holder.tracktotal)
        else:
            track_tagger = ' -metadata track=""'
        if self.tag_holder.disc:
            if self.tag_holder.disctotal:
                disc_tagger = ' -metadata disc="{0}/{1}"'.format(self.tag_holder.disc,
                                                                    self.tag_holder.disctotal)
            else:
                disc_tagger = ' -metadata disc="{}"'.format(self.tag_holder.disc)
        elif self.tag_holder.disctotal:
                disc_tagger = ' -metadata disc="0/{}"'.format(self.tag_holder.disctotal)
        else:
            disc_tagger = ' -metadata disc=""'

        cmd = ''.join(('ffmpeg ',
                        ' -v quiet',
                        ' -i {}'.format(shlex.quote(self.media_entry.path)),
                        ' -i {}'.format(shlex.quote(art_path)) if art_path else '',
                        ' -c copy',
                        ' -map_metadata 0',
                        ' -map 0',
                        ' -map 1' if art_path else '',
                        ' -metadata title="{}"'.format(self.tag_holder.title
                                                        if self.tag_holder.title else ''),
                        ' -metadata album="{}"'.format(self.tag_holder.album
                                                        if self.tag_holder.album else ''),
                        ' -metadata artist="{}"'.format(self.tag_holder.artist
                                                        if self.tag_holder.artist else ''),
                        ' -metadata album_artist="{}"'.format(self.tag_holder.albumartist
                                                        if self.tag_holder.albumartist else ''),
                        ' -metadata genre="{}"'.format(self.tag_holder.genre
                                                        if self.tag_holder.genre else ''),
                        ' -metadata year="{}"'.format(self.tag_holder.year
                                                        if self.tag_holder.year else ''),
                        ' -metadata composer="{}"'.format(self.tag_holder.composer
                                                        if self.tag_holder.composer else ''),
                        ' -metadata encoded_by="{}"'.format(self.tag_holder.encoder
                                                        if self.tag_holder.encoder else ''),

                        ' -metadata BPM="{}"'.format(self.tag_holder.bpm
                                                        if self.tag_holder.bpm else ''),
                        ' -metadata TBPM="{}"'.format(self.tag_holder.bpm
                                                        if self.tag_holder.bpm else ''),
                        ' -metadata compilation="{}"'.format(self.tag_holder.comp
                                                        if self.tag_holder.comp else ''),
                        ' -metadata grouping="{}"'.format(self.tag_holder.grouping
                                                        if self.tag_holder.grouping else ''),
                        ' -metadata comment="{}"'.format(self.tag_holder.comments
                                                        if self.tag_holder.comments else ''),
                        ' -metadata lyrics="{}"'.format(self.tag_holder.lyrics
                                                        if self.tag_holder.lyrics else ''),
                        track_tagger,
                        disc_tagger))
        return cmd

    def artwork_reader(self):
        ''' reads cover art from a media file
        '''
        artwork = None
        if self.media_entry.artwork:
            artwork_stream_idx = self.media_entry.artwork.get('index')
            with temp_dir() as tmp:
                detached_img_path = os.path.join(tmp, 'detached.png')
                cmd = ' '.join(('ffmpeg',
                                    ' -v quiet',
                                    ' -i {}'.format(shlex.quote(self.media_entry.path)),
                                    ' -map 0:{}'.format(artwork_stream_idx),
                                    ' -an',
                                    ' -vcodec copy',
                                    ' {}'.format(detached_img_path)))
                try:
                    output, _ = run_cmd(cmd)
                except CmdProcessingError as e:
                    pass
                else:
                    with open(detached_img_path, 'rb') as img:
                        artwork = img.read()
        return artwork


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


import json, math
from abc import ABCMeta, abstractmethod, abstractproperty
from batchmp.tags.extern.mediafile import MediaFile, UnreadableFileError
from batchmp.ffmptools.ffmputils import (
    ffmpeg_installed,
    run_cmd,
    CmdProcessingError
)
from collections import namedtuple


class Media:
    def __init__(self):
        self.title = None
        self.album = None
        self.artist = None
        self.albumartist = None
        self.genre = None
        self.composer = None
        self.track = None
        self.tracktotal = None
        self.disk = None
        self.disktotal = None
        self.year = None
        self.art = None
        self.length = None
        self.bitrate = None
        self.samplerate = None

class TagHandler(metaclass = ABCMeta):
    def __init__(self):
        self._media = None
        self.mediaHandler = None

    @abstractmethod
    def can_handle(self, mf_name):
        return False

    @abstractmethod
    def save(self):
        pass

    @property
    def title(self):
        return self._media.title
    @title.setter
    def title(self, value):
        self._media.title = value

    @property
    def album(self):
        return self._media.album
    @album.setter
    def album(self, value):
        self._media.album = value

    @property
    def artist(self):
        return self._media.artist
    @artist.setter
    def artist(self, value):
        self._media.artist = value

    @property
    def albumartist(self):
        return self._media.albumartist
    @albumartist.setter
    def albumartist(self, value):
        self._media.albumartist = value

    @property
    def genre(self):
        return self._media.genre
    @genre.setter
    def genre(self, value):
        self._media.genre = value

    @property
    def composer(self):
        return self._media.composer
    @composer.setter
    def composer(self, value):
        self._media.composer = value

    @property
    def track(self):
        return self._media.track
    @track.setter
    def track(self, value):
        self._media.track = value

    @property
    def tracktotal(self):
        return self._media.tracktotal
    @tracktotal.setter
    def tracktotal(self, value):
        self._media.tracktotal = value

    @property
    def disk(self):
        return self._media.disk
    @disk.setter
    def disk(self, value):
        self._media.disk = value

    @property
    def disktotal(self):
        return self._media.disktotal
    @disktotal.setter
    def disktotal(self, value):
        self._media.disktotal = value

    @property
    def year(self):
        return self._media.year
    @year.setter
    def year(self, value):
        self._media.year = value

    @property
    def art(self):
        return self._media.art
    @art.setter
    def art(self, value):
        self._media.art = value

    @property
    def length(self):
        return self._media.length
    @length.setter
    def length(self, value):
        self._media.length = value

    @property
    def bitrate(self):
        return self._media.bitrate
    @bitrate.setter
    def bitrate(self, value):
        self._media.bitrate = value

    @property
    def samplerate(self):
        return self._media.samplerate
    @samplerate.setter
    def samplerate(self, value):
        self._media.samplerate = value


class MutagenTagHandler(TagHandler):
    def _parse_tags(self):
        for field in self.mediaHandler.fields():
            attr = getattr(self.mediaHandler, field)
            if attr:
                setattr(self, field, attr)

        self.bitrate = self.mediaHandler.bitrate
        self.length = self.mediaHandler.length
        self.samplerate = self.mediaHandler.samplerate

    def save(self):
        self.mediaHandler.save()

    def can_handle(self, mf_name):
        try:
            self.mediaHandler = MediaFile(mf_name)
        except UnreadableFileError as error:
            return False
        else:
            self._media = Media()
            self._parse_tags()

        return True

class FFmpegTagHandler(TagHandler):
    FFEntry = namedtuple('FFEntry', ['format', 'audio', 'artwork'])

    def _parse_tags(self):
        if self.mediaHandler.audio:
            if 'bit_rate' in self.mediaHandler.audio:
                self.bitrate = int(self.mediaHandler.audio['bit_rate'])
            elif self.mediaHandler.format and 'bit_rate' in self.mediaHandler.format:
                self.bitrate = int(self.mediaHandler.format['bit_rate'])

            if 'duration' in self.mediaHandler.audio:
                self.length = float(self.mediaHandler.audio['duration'])
            if 'sample_rate' in self.mediaHandler.audio:
                self.samplerate = int(self.mediaHandler.audio['sample_rate'])

        if self.mediaHandler.format:
            # Tags
            tag_info = self.mediaHandler.format['tags'] if 'tags' in self.mediaHandler.format else None
            if tag_info:
                tag_info = {k.lower():v for k,v in tag_info.items()}
                if 'title' in tag_info:
                    self.title = tag_info['title']
                if 'album' in tag_info:
                    self.album = tag_info['album']
                if 'artist' in tag_info:
                    self.artist = tag_info['artist']
                if 'album_artist' in tag_info:
                    self.albumartist = tag_info['album_artist']
                if 'genre' in tag_info:
                    self.genre = tag_info['genre']
                if 'composer' in tag_info:
                    self.composer = tag_info['composer']
                if 'track' in tag_info:
                    track_info = tag_info['track'].split('/')
                    if len(track_info) > 0:
                        self.track = track_info[0]
                        self.tracktotal = track_info[len(track_info) - 1]
                if 'disc' in tag_info:
                    disk_info = tag_info['disc'].split('/')
                    if len(disk_info) > 0:
                        self.disk = disk_info[0]
                        self.disktotal = disk_info[len(disk_info) - 1]
                if 'date' in tag_info:
                    self.year = tag_info['date']

            if self.mediaHandler.artwork:
                self.art = True

    def save(self):
        pass

    def can_handle(self, mf_name):
        if not ffmpeg_installed():
            return False

        p_in = ' '.join(('ffprobe ',
                            '-v quiet',
                            '-show_streams',
                            #'-select_streams a',
                            '-show_format',
                            '-print_format json',
                            '"{}"'.format(mf_name)))
        try:
            output, _ = run_cmd(p_in)
        except CmdProcessingError as e:
            return False
        else:
            format = json.loads(output)['format']

            streams = json.loads(output)['streams']
            audio_stream = {k:v for dict in streams
                                    for k,v in dict.items()
                                        if 'codec_type' in dict and
                                            dict['codec_type'] == 'audio'}
            artwork_stream = {k:v for dict in streams
                                    for k,v in dict.items()
                                        if 'codec_type' in dict and dict['codec_type'] == 'video'
                                            and dict['codec_name'] in ['gif', 'jpeg', 'mjpeg', 'png', 'tiff', 'bmp']}

            self.mediaHandler = self.FFEntry(format, audio_stream, artwork_stream)
            self._media = Media()
            self._parse_tags()

        return True



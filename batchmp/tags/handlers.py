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

class TagHandler(metaclass = ABCMeta):
    def __init__(self):
        self.handledMedia = None
        self._title = None
        self._album = None
        self._artist = None
        self._albumartist = None
        self._genre = None
        self._composer = None
        self._track = None
        self._tracktotal = None
        self._disk = None
        self._disktotal = None
        self._year = None
        self._art = None
        self._length = None
        self._bitrate = None
        self._samplerate = None

    @abstractmethod
    def can_handle(self, mf_name):
        return False

    @abstractmethod
    def save(self):
        pass

    @property
    def title(self):
        return self._title
    @title.setter
    def title(self, value):
        self._title = value

    @property
    def album(self):
        return self._album
    @album.setter
    def album(self, value):
        self._album = value

    @property
    def artist(self):
        return self._artist
    @artist.setter
    def artist(self, value):
        self._artist = value

    @property
    def albumartist(self):
        return self._albumartist
    @albumartist.setter
    def albumartist(self, value):
        self._albumartist = value

    @property
    def genre(self):
        return self._genre
    @genre.setter
    def genre(self, value):
        self._genre = value

    @property
    def composer(self):
        return self._composer
    @composer.setter
    def composer(self, value):
        self._composer = value

    @property
    def track(self):
        return self._track
    @track.setter
    def track(self, value):
        self._track = value

    @property
    def tracktotal(self):
        return self._tracktotal
    @tracktotal.setter
    def tracktotal(self, value):
        self._tracktotal = value

    @property
    def disk(self):
        return self._disk
    @disk.setter
    def disk(self, value):
        self._disk = value

    @property
    def disktotal(self):
        return self._disktotal
    @disktotal.setter
    def disktotal(self, value):
        self._disktotal = value

    @property
    def year(self):
        return self._year
    @year.setter
    def year(self, value):
        self._year = value

    @property
    def art(self):
        return self._art
    @art.setter
    def art(self, value):
        self._art = value

    @property
    def length(self):
        return self._length
    @length.setter
    def length(self, value):
        self._length = value

    @property
    def bitrate(self):
        return self._bitrate
    @bitrate.setter
    def bitrate(self, value):
        self._bitrate = value

    @property
    def samplerate(self):
        return self._samplerate
    @samplerate.setter
    def samplerate(self, value):
        self._samplerate = value


class MutagenTagHandler(TagHandler):
    def _parse_tags(self):
        for field in self.handledMedia.fields():
            attr = getattr(self.handledMedia, field)
            if attr:
                setattr(self, field, attr)

        self.bitrate = self.handledMedia.bitrate
        self.length = self.handledMedia.length
        self.samplerate = self.handledMedia.samplerate

    def save(self):
        self.handledMedia.save()

    def can_handle(self, mf_name):
        try:
            self.handledMedia = MediaFile(mf_name)
        except UnreadableFileError as error:
            return False
        else:
            self._parse_tags()

        return True

class FFmpegTagHandler(TagHandler):
    FFEntry = namedtuple('FFEntry', ['tags', 'audio', 'artwork'])

    def _parse_tags(self):
        if self.handledMedia.audio:
            if 'bit_rate' in self.handledMedia.audio:
                self.bitrate = int(self.handledMedia.audio['bit_rate'])
            if 'duration' in self.handledMedia.audio:
                self.length = float(self.handledMedia.audio['duration'])
            if 'sample_rate' in self.handledMedia.audio:
                self.samplerate = int(self.handledMedia.audio['sample_rate'])

        if self.handledMedia.tags:
            if 'title' in self.handledMedia.tags:
                self.title = self.handledMedia.tags['title']
            if 'album' in self.handledMedia.tags:
                self.album = self.handledMedia.tags['album']
            if 'artist' in self.handledMedia.tags:
                self.artist = self.handledMedia.tags['artist']
            if 'album_artist' in self.handledMedia.tags:
                self.albumartist = self.handledMedia.tags['album_artist']
            if 'genre' in self.handledMedia.tags:
                self.genre = self.handledMedia.tags['genre']
            if 'composer' in self.handledMedia.tags:
                self.composer = self.handledMedia.tags['composer']
            if 'track' in self.handledMedia.tags:
                track_info = self.handledMedia.tags['track'].split('/')
                if len(track_info) > 0:
                    self.track = track_info[0]
                    self.tracktotal = track_info[len(track_info) - 1]
            if 'disc' in self.handledMedia.tags:
                disk_info = self.handledMedia.tags['disc'].split('/')
                if len(disk_info) > 0:
                    self.disk = disk_info[0]
                    self.disktotal = disk_info[len(disk_info) - 1]
            if 'date' in self.handledMedia.tags:
                self.year = self.handledMedia.tags['date']

            if self.handledMedia.artwork:
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
            tag_info = format['tags'] if 'tags' in format else None
            if tag_info:
                tag_info = {k.lower():v for k,v in tag_info.items()}

            streams = json.loads(output)['streams']
            audio_stream = {k:v for dict in streams
                                    for k,v in dict.items()
                                        if 'codec_type' in dict and
                                            dict['codec_type'] == 'audio'}
            artwork_stream = {k:v for dict in streams
                                    for k,v in dict.items()
                                        if 'codec_type' in dict and
                                            dict['codec_type'] == 'video'}

            self.handledMedia = self.FFEntry(tag_info, audio_stream, artwork_stream)
            self._parse_tags()

        return True

# quick dev test
if __name__ == '__main__':
    fpath = ''
    a = FFmpegTagHandler()
    if a.can_handle(fpath):
        print('Title: {}'.format(a.title))
        print('Album: {}'.format(a.album))
        print('Artist: {}'.format(a.artist))
        print('Album Artist: {}'.format(a.albumartist))
        print('Genre: {}'.format(a.genre))
        print('Composer: {}'.format(a.composer))
        print('Track: {}'.format(a.track))
        print('tracktotal: {}'.format(a.tracktotal))
        print('Disk: {}'.format(a.disk))
        print('Disktotal: {}'.format(a.disktotal))
        print('Year: {}'.format(a.year))

        print('Length: {}'.format(a.length))
        print('Bitrate: {}'.format(a.bitrate))
        print('Samplerate: {}'.format(a.samplerate))

        print ('Artwork exists' if a.art else 'No artwork')

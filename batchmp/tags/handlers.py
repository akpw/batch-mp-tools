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

""" Defines Tag Handlers responsibility chain
"""

import os, json, math
from abc import ABCMeta, abstractmethod, abstractproperty
from batchmp.tags.extern.mediafile import MediaFile, UnreadableFileError
from batchmp.ffmptools.ffmputils import (
    ffmpeg_installed,
    run_cmd,
    CmdProcessingError
)
from batchmp.fstools.fsutils import temp_dir
from collections import namedtuple
from weakref import WeakKeyDictionary

# Tag Field Descriptors
class MediaFieldDescriptor:
    def __init__(self):
        self.data = WeakKeyDictionary()
    def __get__(self, obj, type=None):
        return self.data.get(obj)
    def __set__(self, obj, value):
        self.data[obj] = value

# Art is a lazy property
class ArtFieldDescriptor:
    _default_value = object()
    def __init__(self, func):
        self._func = func
    def __get__(self, obj, type=None):
        if obj is None:
            return self
        # this method should only be called on an instance when
        # the property has not yet been set on the instance level
        # so checking the instance dictionary here is probably a bit superfluous...
        value = obj.__dict__.get(self._func.__name__, self._default_value)
        if value is self._default_value:
            # the property has not been set yet
            # calculate the value and store it on instance level
            value = self._func(obj)
            obj.__dict__[self._func.__name__] = value
        return value


class TagHandler(metaclass = ABCMeta):
    ''' Abstract Tag Handler
        Defines supported tags properties & the protocol
    '''
    title = MediaFieldDescriptor()
    album = MediaFieldDescriptor()
    artist = MediaFieldDescriptor()
    albumartist = MediaFieldDescriptor()
    genre = MediaFieldDescriptor()
    composer = MediaFieldDescriptor()
    track = MediaFieldDescriptor()
    tracktotal = MediaFieldDescriptor()
    disk = MediaFieldDescriptor()
    disktotal = MediaFieldDescriptor()
    year = MediaFieldDescriptor()
    length = MediaFieldDescriptor()
    bitrate = MediaFieldDescriptor()
    samplerate = MediaFieldDescriptor()
    channels = MediaFieldDescriptor()
    format = MediaFieldDescriptor()
    encoder = MediaFieldDescriptor()

    def __init__(self):
        self.mediaHandler = None

    @ArtFieldDescriptor
    def art(self):
        ''' default value for the class level property
            specific handlers can override as appropriate
        '''
        return None

    @property
    def has_artwork(self):
        ''' Default impl via direct access
            specific handlers can override for deferred access
        '''
        return self.art

    @abstractmethod
    def can_handle(self, mf_path):
        ''' implement in specific handlers
        '''
        return False

    @abstractmethod
    def save(self):
        ''' implement in specific handlers
        '''
        pass

    @abstractmethod
    def _parse_tags(self):
        ''' implement in specific handlers
        '''
        pass

    def _reset_fields(self):
        ''' clears the tags properties
        '''
        for cls in type(self).__mro__:
            for prop, descr in vars(cls).items():
                if isinstance(descr, MediaFieldDescriptor):
                    setattr(self, prop, None)
                if isinstance(descr, ArtFieldDescriptor):
                    if prop in self.__dict__:
                        del self.__dict__[prop]


class MutagenTagHandler(TagHandler):
    ''' Mutagen-Based Tag Handler
    '''
    def can_handle(self, mf_path):
        ''' Handles the formats supported by Mutagen
        '''
        try:
            self.mediaHandler = MediaFile(mf_path)
        except UnreadableFileError as error:
            return False
        else:
            self._parse_tags()

        return True

    def save(self):
        self.mediaHandler.save()

    def _parse_tags(self):
        ''' copies relevant properties from MediaFile
        '''
        self._reset_fields()
        for field in self.mediaHandler.readable_fields():
            if field in dir(self):
                attr = getattr(self.mediaHandler, field)
                if attr:
                    setattr(self, field, attr)
            #else:
            # dev test
            #    attr = getattr(self.mediaHandler, field)
            #    if attr:
            #        print('Ignoring: {0} with value: {1}'.format(field, attr))


class FFmpegTagHandler(TagHandler):
    ''' FFmpeg-Based Tag Handler
    '''

    FFEntry = namedtuple('FFEntry', ['mf_path', 'format', 'audio', 'artwork'])

    def can_handle(self, mf_path):
        if not ffmpeg_installed():
            return False

        cmd = ' '.join(('ffprobe ',
                            '-v quiet',
                            '-show_streams',
                            #'-select_streams a',
                            '-show_format',
                            '-print_format json',
                            '"{}"'.format(mf_path)))
        try:
            output, _ = run_cmd(cmd)
        except CmdProcessingError as e:
            return False
        else:
            format = json.loads(output).get('format')

            streams = json.loads(output)['streams']
            audio_stream = {k:v for dict in streams
                                    for k,v in dict.items()
                                        if 'codec_type' in dict and
                                            dict['codec_type'] == 'audio'}
            artwork_stream = {k:v for dict in streams
                                    for k,v in dict.items()
                                        if 'codec_type' in dict and dict['codec_type'] == 'video'
                                            and dict['codec_name'] in ('gif', 'jpeg', 'mjpeg', 'png', 'tiff', 'bmp')}

            self.mediaHandler = self.FFEntry(mf_path, format, audio_stream, artwork_stream)
            self._parse_tags()

        return True

    def save(self):
        ''' Coming soon :)
        '''
        pass

    @ArtFieldDescriptor
    def art(self):
        ''' detauch cover art from a media file
            and store it as an instance property via ArtFieldDescriptor
        '''
        artwork = None
        if self.has_artwork:
            with temp_dir() as tmp:
                detached_img_path = os.path.join(tmp, 'detached.png')
                cmd = ' '.join(('ffmpeg ',
                                    '-v quiet',
                                    '-i "{}"'.format(self.mediaHandler.mf_path),
                                    '-an',
                                    '-vcodec copy',
                                    '{}'.format(detached_img_path)))
                try:
                    output, _ = run_cmd(cmd)
                except CmdProcessingError as e:
                    pass
                else:
                    with open(detached_img_path, 'rb') as img:
                        artwork = img.read()
        return artwork

    @property
    def has_artwork(self):
        ''' deferred access to the art property
        '''
        return self.mediaHandler.artwork

    def _parse_tags(self):
        ''' parses tags from FFmpeg output
        '''
        self._reset_fields()

        # the audio stream info
        if self.mediaHandler.audio:
            if 'bit_rate' in self.mediaHandler.audio:
                self.bitrate = int(self.mediaHandler.audio['bit_rate'])
            elif self.mediaHandler.format:
                self.bitrate = int(self.mediaHandler.format.get('bit_rate', 0))

            self.length = float(self.mediaHandler.audio.get('duration', 0.0))
            self.samplerate = int(self.mediaHandler.audio.get('sample_rate', 0))

            self.channels = self.mediaHandler.audio.get('channels')
            self.format = self.mediaHandler.audio['codec_name']
            if self.format:
                self.format = self.format.upper()
            self.encoder = self.mediaHandler.audio.get('codec_long_name')


        # Tags
        if self.mediaHandler.format:
            tag_info = self.mediaHandler.format['tags'] if 'tags' in self.mediaHandler.format else None
            if tag_info:
                tag_info = {k.lower():v for k,v in tag_info.items()}

                self.title = tag_info.get('title')
                self.album = tag_info.get('album')
                self.artist = tag_info.get('artist')
                self.albumartist = tag_info.get('album_artist')
                self.genre = tag_info.get('genre')
                self.year = tag_info.get('date')
                self.composer = tag_info.get('composer')

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


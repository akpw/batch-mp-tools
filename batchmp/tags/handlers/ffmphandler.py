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

""" Tag Handlers responsibility chain
"""

import os, json, shutil
from collections import namedtuple
from batchmp.ffmptools.ffmputils import (
    ffmpeg_installed,
    run_cmd,
    CmdProcessingError
)
from batchmp.fstools.fsutils import temp_dir
from batchmp.tags.handlers.basehandler import (
    TagHandler,
    ArtFieldDescriptor)

class FFmpegTagHandler(TagHandler):
    ''' FFmpeg-Based Tag Handler
    '''
    FFEntry = namedtuple('FFEntry', ['path', 'format', 'audio', 'artwork'])

    def can_handle(self, path):
        self._reset_fields()
        if not ffmpeg_installed():
            return False

        cmd = ''.join(('ffprobe ',
                            ' -v quiet',
                            ' -show_streams',
                            #' -select_streams a',
                            ' -show_format',
                            ' -print_format json',
                            ' "{}"'.format(path)))
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
            if not audio_stream:
                return False

            artwork_stream = {k:v for dict in streams
                                    for k,v in dict.items()
                                        if 'codec_type' in dict and dict['codec_type'] == 'video'
                                            and dict['codec_name'] in ('gif', 'jpeg', 'mjpeg', 'png', 'tiff', 'bmp')}

            self.mediaHandler = self.FFEntry(path, format, audio_stream, artwork_stream)
            self._parse_tags()
        return True

    def _parse_tags(self):
        ''' parses tags from FFmpeg output
        '''
        if self.mediaHandler.audio:
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
                    disc_info = tag_info['disc'].split('/')
                    if len(disc_info) > 0:
                        self.disc = disc_info[0]
                        self.disctotal = disc_info[len(disc_info) - 1]

    def save(self):
        ''' saves tags
        '''
        with temp_dir() as tmp:
            tmp_fpath = os.path.join(tmp, os.path.basename(self.mediaHandler.path))

            art_writer = self.can_write_artwork and self.art
            if art_writer:
                art_path = self.detauch_art(dir_path = tmp)

            track_tagger = disc_tagger = ''
            if self.track:
                if self.tracktotal:
                    track_tagger = ' -metadata track="{0}/{1}"'.format(self.track, self.tracktotal)
                else:
                    track_tagger = ' -metadata track="{}"'.format(self.track)
            elif self.tracktotal:
                    track_tagger = ' -metadata track="0/{}"'.format(self.tracktotal)
            else:
                track_tagger = ''
            if self.disc:
                if self.disctotal:
                    disc_tagger = ' -metadata disc="{0}/{1}"'.format(self.disc, self.disctotal)
                else:
                    disc_tagger = ' -metadata disc="{}"'.format(self.disc)
            elif self.disctotal:
                    disc_tagger = ' -metadata disc="0/{}"'.format(self.disctotal)
            else:
                disc_tagger = ''

            cmd = ''.join(('ffmpeg ',
                            #' -v quiet',
                            ' -i "{}"'.format(self.mediaHandler.path),
                            ' -i "{}"'.format(art_path) if art_writer else '',
                            ' -c copy',
                            ' -map_metadata 0',
                            ' -map 0',
                            ' -map 1' if art_writer else '',
                            ' -metadata title="{}"'.format(self.title),
                            ' -metadata album="{}"'.format(self.album),
                            ' -metadata artist="{}"'.format(self.artist),
                            ' -metadata album_artist="{}"'.format(self.albumartist),
                            ' -metadata genre="{}"'.format(self.genre),
                            ' -metadata year="{}"'.format(self.year),
                            ' -metadata composer="{}"'.format(self.composer),
                            track_tagger,
                            disc_tagger,
                            ' "{}"'.format(tmp_fpath)))
            try:
                failed = False
                output, _ = run_cmd(cmd)
            except CmdProcessingError as e:
                if self.can_write_artwork:
                    self.can_write_artwork = False
                    self.save()
                    return
                else:
                    failed = True
            else:
                try:
                    shutil.move(tmp_fpath, self.mediaHandler.path)
                except OSError as e:
                    raise e

            if failed:
                print ('FFMP: could not process {}'.format(self.mediaHandler.path))
            else:
                if not self.can_write_artwork:
                    print ('FFMP: skipped artwork for {}'.format(self.mediaHandler.path))

    @ArtFieldDescriptor
    def art(self):
        ''' detauch cover art from a media file and store it
            as an instance property via ArtFieldDescriptor
        '''
        artwork = None
        if self.has_artwork:
            with temp_dir() as tmp:
                detached_img_path = os.path.join(tmp, 'detached.png')
                cmd = ' '.join(('ffmpeg ',
                                    '-v quiet',
                                    '-i "{}"'.format(self.mediaHandler.path),
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
        return self.mediaHandler.artwork != None if self.mediaHandler else None

    @property
    def length(self):
        audio = 0.0
        if self.mediaHandler.audio:
            audio = float(self.mediaHandler.audio.get('duration', 0.0))
        return audio

    @property
    def bitrate(self):
        bitrate = 0
        if self.mediaHandler.audio:
            if 'bit_rate' in self.mediaHandler.audio:
                bitrate = int(self.mediaHandler.audio['bit_rate'])
            elif self.mediaHandler.format:
                bitrate = int(self.mediaHandler.format.get('bit_rate', 0))
        return bitrate

    @property
    def bitdepth(self):
        bitdepth = 0
        if self.mediaHandler.audio:
            if 'bits_per_sample' in self.mediaHandler.audio:
                bitdepth = int(self.mediaHandler.audio.get('bits_per_sample', 0))
        return bitdepth

    @property
    def samplerate(self):
        samplerate = 0
        if self.mediaHandler.audio:
            samplerate = int(self.mediaHandler.audio.get('sample_rate', 0))
        return samplerate

    @property
    def channels(self):
        channels = 0
        if self.mediaHandler.audio:
            channels = self.mediaHandler.audio.get('channels')
        return channels

    @property
    def format(self):
        format = None
        if self.mediaHandler.audio:
            format = self.mediaHandler.audio['codec_name']
            if format:
                format = format.upper()
        return format



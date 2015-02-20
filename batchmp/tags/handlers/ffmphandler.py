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
from batchmp.tags.handlers.basehandler import TagHandler

class FFmpegTagHandler(TagHandler):
    ''' FFmpeg-Based Tag Handler
    '''
    FFEntry = namedtuple('FFEntry', ['path', 'format', 'audio', 'artwork'])

    def _can_handle(self, path):
        self._reset_handler()
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
        #print('ffmpeg can handle')
        return True

    def _parse_tags(self):
        ''' parses tags from FFmpeg output
        '''
        # non-tagable fields defaults
        self.tag_holder.length = 0.0
        self.tag_holder.bitrate = 0
        self.tag_holder.samplerate = 0
        self.tag_holder.channels = 0
        self.tag_holder.bitdepth = 0

        # Tags
        if self.mediaHandler.format:
            self.tag_holder.bitrate = int(self.mediaHandler.format.get('bit_rate', 0))

            tag_info = self.mediaHandler.format['tags'] if 'tags' in self.mediaHandler.format else None
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

        # Non-taggable fields
        if self.mediaHandler.audio:
            self.tag_holder.length = float(self.mediaHandler.audio.get('duration', 0.0))
            self.tag_holder.bitrate = int(self.mediaHandler.audio.get('bit_rate', 0))
            self.tag_holder.samplerate = int(self.mediaHandler.audio.get('sample_rate', 0))
            self.tag_holder.bitdepth = int(self.mediaHandler.audio.get('bits_per_sample', 0))
            self.tag_holder.channels = int(self.mediaHandler.audio.get('channels', 0))

            format = self.mediaHandler.audio.get('codec_name')
            if format:
                self.tag_holder.format = format.upper()

        # Art
        if self.mediaHandler.artwork:
            self.tag_holder.deferred_art_method = self.artwork_reader

    def _save(self):
        ''' saves tags
        '''
        #print('saving via ff')
        with temp_dir() as tmp:
            tmp_fpath = os.path.join(tmp, os.path.basename(self.mediaHandler.path))

            art_writer = self._can_write_artwork and self.tag_holder.art
            if art_writer:
                art_path = self.detauch_art(dir_path = tmp)

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
                            #' -v quiet',
                            ' -i "{}"'.format(self.mediaHandler.path),
                            ' -i "{}"'.format(art_path) if art_writer else '',
                            ' -c copy',
                            ' -map_metadata 0',
                            ' -map 0',
                            ' -map 1' if art_writer else '',
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
                            track_tagger,
                            disc_tagger,
                            ' "{}"'.format(tmp_fpath)))
            try:
                failed = False
                output, _ = run_cmd(cmd)
            except CmdProcessingError as e:
                if self._can_write_artwork:
                    self._can_write_artwork = False
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
                if not self._can_write_artwork:
                    print ('FFMP: skipped artwork for {}'.format(self.mediaHandler.path))

    def artwork_reader(self):
        ''' reads cover art from a media file
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

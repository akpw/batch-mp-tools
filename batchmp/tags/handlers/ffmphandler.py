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
from batchmp.tags.handlers.ffmphandlers.base import FFBaseFormatHandler

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
                                            and dict['codec_name'] in ('jpeg', 'png', 'gif', 'tiff', 'bmp', 'mjpeg')}

            media_entry = self.FFEntry(path, format, audio_stream, artwork_stream)
            self._media_handler = FFBaseFormatHandler(self.tag_holder) #... + FFSpecificFormatHandler() + ...
            if self._media_handler.can_handle(media_entry):
                self._media_handler.parse()
                return True
            else:
                return False

    def _save(self, write_artwork = True):
        ''' saves tags
        '''
        if not self._media_handler:
            return

        with temp_dir() as tmp:
            tmp_fpath = os.path.join(tmp, os.path.basename(self._media_handler.path))

            artwork_writer = write_artwork and self.tag_holder.art
            art_path = self.detauch_art(dir_path = tmp) if artwork_writer else None

            save_cmd = self._media_handler.build_save_cmd(art_path = art_path)
            save_cmd = ''.join((save_cmd, ' "{}"'.format(tmp_fpath)))

            try:
                failed = False
                output, _ = run_cmd(save_cmd)
            except CmdProcessingError as e:
                if artwork_writer:
                    self._save(write_artwork = False)
                    return
                else:
                    failed = True
            else:
                try:
                    shutil.move(tmp_fpath, self._media_handler.path)
                except OSError as e:
                    raise e

            if failed:
                print ('FFMP: could not process {}'.format(self._media_handler.path))
            else:
                if not write_artwork:
                    print ('FFMP: skipped artwork for {}'.format(self._media_handler.path))











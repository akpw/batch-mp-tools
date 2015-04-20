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


import os, shutil
from batchmp.commons.utils import temp_dir
from batchmp.tags.handlers.basehandler import TagHandler
from batchmp.tags.handlers.ffmphandlers.base import FFBaseFormatHandler
from batchmp.ffmptools.ffutils import FFH
from batchmp.commons.utils import run_cmd, CmdProcessingError


class FFmpegTagHandler(TagHandler):
    ''' FFmpeg-Based Tag Handler
    '''
    def _can_handle(self, path):
        self._reset_handler()
        media_entry = FFH.media_file_info(path)
        if media_entry:
            self._media_handler = FFBaseFormatHandler(self.tag_holder) #... + FFSpecificFormatHandler() + ...
            if self._media_handler.can_handle(media_entry):
                self.tag_holder.filepath = path
                self._media_handler.parse()
                return True
        return False

    def _save(self, write_artwork = True):
        ''' saves tags
        '''
        if not self._media_handler:
            return

        with temp_dir() as tmp:
            tmp_fpath = os.path.join(tmp, os.path.basename(self._media_handler.path))

            artwork_writer = write_artwork and \
                             self._media_handler.artwork_writer_supported_format and \
                             self.tag_holder.art
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




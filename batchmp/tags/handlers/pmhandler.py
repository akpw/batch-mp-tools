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


from batchmp.ffmptools.ffutils import FFH
from batchmp.tags.handlers.basehandler import TagHandler
from batchmp.fstools.builders.fsentry import FSMediaEntryType


class PlayableMediaHandler(TagHandler):
    ''' Playable Media Cheker
    '''
    def _can_handle(self, path):
        ''' Quick check for right media types to handle
        '''
        media_type = FFH.media_type(fpath = path, fast_scan = True)

        supported_media = media_type in (FSMediaEntryType.VIDEO, FSMediaEntryType.AUDIO)
        if media_type in (FSMediaEntryType.VIDEO, FSMediaEntryType.AUDIO):
            return True

        return False


        


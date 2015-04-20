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


from batchmp.tags.extern.mediafile import MediaFile, UnreadableFileError
from batchmp.tags.extern.mediafile import MutagenError
from batchmp.tags.handlers.basehandler import TagHandler


class MutagenTagHandler(TagHandler):
    ''' Mutagen-Based Tag Handler
    '''
    def _can_handle(self, path):
        ''' Handles the formats supported by Mutagen
        '''
        self._reset_handler()
        try:
            self._media_handler = MediaFile(path)
        except UnreadableFileError as error:
            return False
        else:
            self.tag_holder.filepath = path
            self._parse_tags()
        return True

    def _parse_tags(self):
        ''' copies relevant properties from Mutagen MediaFile
        '''
        for field in self._media_handler.readable_fields():
            if field in dir(self.tag_holder):
                attr = getattr(self._media_handler, field)
                if attr:
                    setattr(self.tag_holder, field, attr)
            #else:
            # dev test
            #    attr = getattr(self._media_handler, field)
            #    if attr:
            #        print('Ignoring: {0} with value: {1}'.format(field, attr))

    def _save(self):
        if self._media_handler:
            for field in self.tag_holder.taggable_fields():
                value = getattr(self.tag_holder, field)
                setattr(self._media_handler, field, value)

            self._media_handler.save()


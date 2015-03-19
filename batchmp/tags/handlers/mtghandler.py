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


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
from batchmp.tags.extern.mediafile import MediaFile, UnreadableFileError
from batchmp.tags.extern.mediafile import MutagenError, Image, ImageType
from batchmp.tags.handlers.basehandler import (
    TagHandler,
    ArtFieldDescriptor)

class MutagenTagHandler(TagHandler):
    ''' Mutagen-Based Tag Handler
    '''
    def can_handle(self, path):
        ''' Handles the formats supported by Mutagen
        '''
        self._reset_fields()
        try:
            self.mediaHandler = MediaFile(path)
        except UnreadableFileError as error:
            return False
        else:
            self._parse_tags()
        return True

    def _parse_tags(self):
        ''' copies relevant properties from MediaFile
        '''
        for field in self.mediaHandler.fields():
            if field in dir(self):
                attr = getattr(self.mediaHandler, field)
                if attr:
                    setattr(self, field, attr)
            #else:
            # dev test
            #    attr = getattr(self.mediaHandler, field)
            #    if attr:
            #        print('Ignoring: {0} with value: {1}'.format(field, attr))

    # Read-only properties
    @property
    def length(self):
        return self.mediaHandler.length
    @property
    def bitrate(self):
        return self.mediaHandler.bitrate
    @property
    def bitdepth(self):
        return self.mediaHandler.bitdepth
    @property
    def samplerate(self):
        return self.mediaHandler.samplerate
    @property
    def channels(self):
        return self.mediaHandler.channels
    @property
    def format(self):
        return self.mediaHandler.format

    def save(self):
        for field in self.fields():
            value = getattr(self, field)
            setattr(self.mediaHandler, field, value)

        self.mediaHandler.save()







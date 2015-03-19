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
import os
from enum import Enum
from batchmp.commons.chainedhandler import ChainedHandler
from abc import abstractmethod
from batchmp.fstools.fsutils import UniqueDirNamesChecker
from batchmp.commons.descriptors import LazyTypedPropertyDescriptor


class DetauchedArtType(Enum):
    ''' Detached art type specifier
    '''
    PNG, JPEG = 0, 1
    @staticmethod
    def art_ext(type):
        if type == DetauchedArtType.JPEG:
            return '.jpg'
        else:
            return '.png'


class TagHandler(ChainedHandler):
    tag_holder = LazyTypedPropertyDescriptor('batchmp.tags.handlers.tagsholder.TagHolder')

    def __init__(self):
        self._media_handler = None

    def __add__(self, tag_handler):
        tag_handler.tag_holder = self.tag_holder
        return super().__add__(tag_handler)

    def _can_handle(self, path):
        return False

    # Tag Handler operations
    def save(self):
        self.responder._save()

    @abstractmethod
    def _save(self):
        ''' implement in specific tag handlers
        '''
        pass

    # Helpers
    def _reset_handler(self):
        ''' resets the handler
        '''
        self._media_handler = None
        self.tag_holder.reset_tags()

    def copy_tags(self, tag_holder = None):
        ''' copies tags from a tag_holder
        '''
        self.tag_holder.copy_tags(tag_holder = tag_holder)

    def clear_tags(self):
        ''' clear tags values
        '''
        self.tag_holder.clear_tags()

    def detauch_art(self, dir_path = None, type = None):
        ''' detauches art, returning art file path
        '''
        if not type or (type not in DetauchedArtType):
            type = DetauchedArtType.PNG
        art_path = None
        if self.tag_holder.art:
            if not dir_path:
                dir_path = os.path.basename(self._media_handler.path)
            fname = os.path.splitext(os.path.basename(self._media_handler.path))[0] + DetauchedArtType.art_ext(type)
            fname = UniqueDirNamesChecker(dir_path).unique_name(fname)

            art_path = os.path.join(dir_path, fname)
            with open(art_path, 'wb') as f:
                f.write(self.tag_holder.art)
        return art_path

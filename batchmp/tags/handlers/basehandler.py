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
from abc import ABCMeta, abstractmethod
from batchmp.fstools.fsutils import UniqueDirNamesChecker
from batchmp.commons.descriptors import LazyClassPropertyDescriptor, LazyFunctionPropertyDescriptor
from weakref import ref, ReferenceType

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

class TagHandler(metaclass = ABCMeta):
    ''' Responsibilty Chain for Tag Handlers
    '''
    class THChainDispatcher:
        ''' Internal dispatcher for chained handlers
        '''
        def __init__(self):
            self._handlers_refs_chain = []
            self._receiver_idx = -1

        def add_handler(self, tag_handler):
            if not isinstance(tag_handler, TagHandler):
                raise TypeError('TagHandler.__add__() expects a TagHandler instance')
            else:
                if len(self._handlers_refs_chain) == 0:
                    self._handlers_refs_chain.append(ref(tag_handler))
                else:
                    self._handlers_refs_chain.append(tag_handler)

        def has_responder(self, mfname):
            ''' Returns suitable handler for a media file
            '''
            for idx, handler in enumerate(self._handlers_refs_chain):
                if type(handler) is ReferenceType:
                    handler = handler()
                if handler and handler._can_handle(mfname):
                    self._receiver_idx = idx
                    return True
            return False

        @property
        def responder(self):
            if self._receiver_idx >= 0:
                handler = self._handlers_refs_chain[self._receiver_idx]
                if type(handler) is ReferenceType:
                    handler = handler()
                return handler
            else:
                return None

    tag_holder = LazyClassPropertyDescriptor('batchmp.tags.handlers.tagsholder.TagHolder')

    def __init__(self):
        self._mediaHandler = None
        self._can_write_artwork = True

    def _reset_handler(self):
        self._mediaHandler = None
        self._can_write_artwork = True
        if 'tag_holder' in self.__dict__:
            del self.__dict__['tag_holder']

    @LazyFunctionPropertyDescriptor
    def _handler_chain(self):
        handler_chain = TagHandler.THChainDispatcher()
        handler_chain.add_handler(self)
        return handler_chain

    def __add__(self, tag_handler):
        ''' Adds a handler to hanlders chain
        '''
        if not isinstance(tag_handler, TagHandler):
            raise TypeError('TagHandler.__add__() expects a TagHandler instance')
        tag_handler._handler_chain = self._handler_chain
        tag_handler.tag_holder = self.tag_holder
        self._handler_chain.add_handler(tag_handler)

        return self

    def can_handle(self, path):
        return self._handler_chain.has_responder(path)

    def save(self):
        self._handler_chain.responder._save()

    # Abstract methods
    @abstractmethod
    def _can_handle(self, path):
        ''' implement in specific handlers
        '''
        return False

    # Abstract methods
    @abstractmethod
    def _save(self):
        ''' implement in specific handlers
        '''
        return False

    # Helper methods
    def copy_tags(self, tag_holder, copy_empty_vals = False):
        self.tag_holder.copy_tags(tag_holder)

    def clear_tags(self):
        self.tag_holder.clear_tags()

    def detauch_art(self, dir_path = None, type = DetauchedArtType.PNG):
        fpath = None
        if self.tag_holder.art:
            if not dir_path:
                dir_path = os.path.basename(self.mediaHandler.path)
            fname = os.path.splitext(os.path.basename(self.mediaHandler.path))[0] + DetauchedArtType.art_ext(type)
            fname = UniqueDirNamesChecker(dir_path).unique_name(fname)

            fpath = os.path.join(dir_path, fname)
            with open(fpath, 'wb') as f:
                f.write(self.tag_holder.art)

        return fpath

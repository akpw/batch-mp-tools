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
from abc import ABCMeta, abstractmethod, abstractproperty
from weakref import WeakKeyDictionary
from batchmp.fstools.fsutils import UniqueDirNamesChecker


# Tag Field Descriptors
class MediaFieldDescriptor:
    def __init__(self):
        self.data = WeakKeyDictionary()
    def __get__(self, obj, type=None):
        return self.data.get(obj)
    def __set__(self, obj, value):
        self.data[obj] = value

# Art Field (lazy property)
class ArtFieldDescriptor:
    _default_value = object()
    def __init__(self, func):
        self._func = func
    def __get__(self, obj, type=None):
        if obj is None:
            return self
        # this method should only be called on an instance when
        # the property has not yet been set on the instance level
        # so checking the instance dictionary here is probably a bit superfluous...
        value = obj.__dict__.get(self._func.__name__, self._default_value)
        if value is self._default_value:
            # the property has not been set yet
            # calculate the value and store it on the instance level
            value = self._func(obj)
            obj.__dict__[self._func.__name__] = value
        return value


class ArtType(Enum):
    PNG, JPEG = 0, 1

    @staticmethod
    def art_ext(type):
        if type == ArtType.JPEG:
            return '.jpg'
        else:
            return '.png'


class TagHandler(metaclass = ABCMeta):
    ''' Abstract Tag Handler
        Defines supported tags properties & the protocol
    '''
    title = MediaFieldDescriptor()
    album = MediaFieldDescriptor()
    artist = MediaFieldDescriptor()
    albumartist = MediaFieldDescriptor()
    genre = MediaFieldDescriptor()
    composer = MediaFieldDescriptor()
    track = MediaFieldDescriptor()
    tracktotal = MediaFieldDescriptor()
    disc = MediaFieldDescriptor()
    disctotal = MediaFieldDescriptor()
    year = MediaFieldDescriptor()
    encoder = MediaFieldDescriptor()

    def __init__(self):
        self.mediaHandler = None
        self.can_write_artwork = True

    @ArtFieldDescriptor
    def art(self):
        ''' default value for the class level property
            specific handlers can override as appropriate
        '''
        return None

    # Read-only properties
    @property
    def has_artwork(self):
        ''' Default impl via direct access
            specific handlers can override for deferred access
        '''
        return self.art
    @property
    def length(self):
        return 0
    @property
    def bitrate(self):
        return 0
    @property
    def samplerate(self):
        return 0
    @property
    def channels(self):
        return 0
    @property
    def bitdepth(self):
        return 0
    @property
    def format(self):
        return None

    # Abstract methods
    @abstractmethod
    def can_handle(self, path):
        ''' implement in specific handlers
        '''
        return False

    @abstractmethod
    def save(self):
        ''' implement in specific handlers
        '''
        pass

    @classmethod
    def fields(cls):
        ''' generates names of all writable tag properties
        '''
        for c in cls.__mro__:
            for prop, descr in vars(c).items():
                if isinstance(descr, MediaFieldDescriptor):
                    yield prop
                if isinstance(descr, ArtFieldDescriptor):
                    yield prop

    @classmethod
    def readable_fields(cls):
        ''' generates names of all tag properties
        '''
        for prop in cls.fields():
            yield prop
        for prop in ('has_artwork', 'length', 'samplerate', 'bitdepth',  'channels', 'format'):
            yield prop

    def _reset_fields(self):
        ''' clears the tags properties
        '''
        self.mediaHandler = None
        self.can_write_artwork = True

        for cls in type(self).__mro__:
            for prop, descr in vars(cls).items():
                if isinstance(descr, MediaFieldDescriptor):
                    setattr(self, prop, None)
                if isinstance(descr, ArtFieldDescriptor):
                    if prop in self.__dict__:
                        del self.__dict__[prop]

    def copy_fields(self, tag_holder, copy_empty_vals = False):
            ''' copies tags from passed tag_holder object
            '''
            for field in self.fields():
                if hasattr(tag_holder, field):
                    value = getattr(tag_holder, field)
                    if value != None or copy_empty_vals:
                        setattr(self, field, value)

    def remove_tags(self):
        ''' clears the tags properties
        '''
        for cls in type(self).__mro__:
            for prop, descr in vars(cls).items():
                if isinstance(descr, MediaFieldDescriptor) or isinstance(descr, ArtFieldDescriptor):
                    setattr(self, prop, None)

    def detauch_art(self, dir_path = None, type = ArtType.PNG):
        fpath = None
        if self.art:
            if not dir_path:
                dir_path = os.path.basename(self.mediaHandler.path)
            fname = os.path.splitext(os.path.basename(self.mediaHandler.path))[0] + ArtType.art_ext(type)
            fname = UniqueDirNamesChecker(dir_path).unique_name(fname)

            fpath = os.path.join(dir_path, fname)
            with open(fpath, 'wb') as f:
                f.write(self.art)

        return fpath


class TagHolder(TagHandler):
    ''' Minimal Base Handler impl
        Useful for passing tag values around
    '''
    def can_handle(self, path):
        return False
    def save(self):
        pass





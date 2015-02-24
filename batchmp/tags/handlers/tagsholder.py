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

""" Tags Holder
"""

from weakref import WeakMethod
from types import MethodType
from itertools import chain
from batchmp.commons.descriptors import PropertyDescriptor, LazyFunctionPropertyDescriptor

# Tag Field Descriptors
class TaggableMediaFieldDescriptor(PropertyDescriptor):
    pass

class NonTaggableMediaFieldDescriptor(PropertyDescriptor):
    pass

# Art Field is a lazy property
class ArtFieldDescriptor(LazyFunctionPropertyDescriptor):
    pass

class TagHolder:
    ''' Abstract Tag Handler
        Defines supported tags & the protocol
    '''
    title = TaggableMediaFieldDescriptor()
    album = TaggableMediaFieldDescriptor()
    artist = TaggableMediaFieldDescriptor()
    albumartist = TaggableMediaFieldDescriptor()
    genre = TaggableMediaFieldDescriptor()
    composer = TaggableMediaFieldDescriptor()
    track = TaggableMediaFieldDescriptor()
    tracktotal = TaggableMediaFieldDescriptor()
    disc = TaggableMediaFieldDescriptor()
    disctotal = TaggableMediaFieldDescriptor()
    year = TaggableMediaFieldDescriptor()
    encoder = TaggableMediaFieldDescriptor()

    bpm = TaggableMediaFieldDescriptor()
    comp = TaggableMediaFieldDescriptor()
    grouping = TaggableMediaFieldDescriptor()
    comments = TaggableMediaFieldDescriptor()
    lyrics = TaggableMediaFieldDescriptor()

    # non-taggable fields
    length = NonTaggableMediaFieldDescriptor()
    bitrate = NonTaggableMediaFieldDescriptor()
    samplerate = NonTaggableMediaFieldDescriptor()
    channels = NonTaggableMediaFieldDescriptor()
    bitdepth = NonTaggableMediaFieldDescriptor()
    format = NonTaggableMediaFieldDescriptor()

    def __init__(self):
        self._deferred_art_method_wref = None

    # Art field supports deferred access
    @property
    def deferred_art_method(self):
        if self._deferred_art_method_wref:
            return self._deferred_art_method_wref()
        else:
            return None
    @deferred_art_method.setter
    def deferred_art_method(self, value):
        if type(value) is MethodType:
            self._deferred_art_method_wref = WeakMethod(value)
        else:
            self._deferred_art_method_wref = None

    @property
    def has_artwork(self):
        ''' when art retrieval is deffered,
            provides info on art presence whithout loading into memory
        '''
        if self.deferred_art_method:
            return True
        elif self.art:
            return True
        return False

    @ArtFieldDescriptor
    def art(self):
        ''' provides access on the class level
            when art is set on the instance level, should be ignored
        '''
        return self.deferred_art_method

    @classmethod
    def taggable_fields(cls):
        ''' generates names of all writable tag fields
        '''
        for c in cls.__mro__:
            for field, descr in vars(c).items():
                if isinstance(descr, TaggableMediaFieldDescriptor):
                    yield field
                elif isinstance(descr, ArtFieldDescriptor):
                    yield field

    @classmethod
    def non_taggable_fields(cls):
        for c in cls.__mro__:
            for field, descr in vars(c).items():
                if isinstance(descr, NonTaggableMediaFieldDescriptor):
                    yield field

    @classmethod
    def fields(cls):
        for field in chain(cls.taggable_fields, cls.non_taggable_fields):
            yield field

    def copy_tags(self, tag_holder = None, copy_non_taggable = False, copy_empty_vals = False):
            ''' copies tags from passed tag_holder object
            '''
            fields = self.fields if copy_non_taggable else self.taggable_fields
            for field in fields():
                if hasattr(tag_holder, field):
                    value = getattr(tag_holder, field)
                    if value != None or copy_empty_vals:
                        setattr(self, field, value)

    def clear_tags(self, reset_art = False):
        ''' clears writable tags values
        '''
        for field in self.taggable_fields():
            setattr(self, field, None)
            if reset_art and hasattr(self, 'art'):
                del self.art

    def reset_tags(self):
        self.clear_tags(reset_art = True)


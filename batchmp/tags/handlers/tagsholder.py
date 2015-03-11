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

from weakref import WeakMethod
from types import MethodType
from itertools import chain
from string import Template
from batchmp.commons.descriptors import PropertyDescriptor, LazyFunctionPropertyDescriptor

# Tag Field Descriptors
class TaggableMediaFieldDescriptor(PropertyDescriptor):
    pass

class ExpandableMediaFieldDescriptor(TaggableMediaFieldDescriptor):
    def __set__(self, instance, value):
        if value:
            value = instance._expand_templates(value)
        self.data[instance] = value

class NonTaggableMediaFieldDescriptor(PropertyDescriptor):
    pass

# Art Field is a lazy property
class ArtFieldDescriptor(LazyFunctionPropertyDescriptor):
    pass

class TagHolder:
    ''' Abstract Tag Handler
        Defines supported tags & the protocol
    '''
    title = ExpandableMediaFieldDescriptor()
    album = ExpandableMediaFieldDescriptor()
    artist = ExpandableMediaFieldDescriptor()
    albumartist = ExpandableMediaFieldDescriptor()
    genre = ExpandableMediaFieldDescriptor()
    composer = ExpandableMediaFieldDescriptor()
    track = TaggableMediaFieldDescriptor()
    tracktotal = TaggableMediaFieldDescriptor()
    disc = TaggableMediaFieldDescriptor()
    disctotal = TaggableMediaFieldDescriptor()
    year = TaggableMediaFieldDescriptor()
    encoder = ExpandableMediaFieldDescriptor()

    bpm = TaggableMediaFieldDescriptor()
    comp = TaggableMediaFieldDescriptor()
    grouping = ExpandableMediaFieldDescriptor()
    comments = ExpandableMediaFieldDescriptor()
    lyrics = ExpandableMediaFieldDescriptor()

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
        ''' when art retrieval is deferred,
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
        if self.deferred_art_method:
            return self.deferred_art_method()
        else:
            return None

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
            if not tag_holder:
                return
            fields = self.fields if copy_non_taggable else self.taggable_fields
            for field in fields():
                if hasattr(tag_holder, field):
                    value = getattr(tag_holder, field)
                    if value or copy_empty_vals:
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


    # Internal Helpers
    def _expand_templates(self, value):
        template = Template(value)
        return template.safe_substitute(self._substitute_dictionary)

    @property
    def _substitute_dictionary(self):
        sd = {}
        if self.title:
            sd['title'] = self.title
        if self.album:
            sd['album'] = self.album
        if self.artist:
            sd['artist'] = self.artist
        if self.albumartist:
            sd['albumartist'] = self.albumartist
        if self.genre:
            sd['genre'] = self.genre
        if self.composer:
            sd['composer'] = self.composer
        if self.track:
            sd['track'] = self.track
        if self.tracktotal:
            sd['tracktotal'] = self.tracktotal
        if self.disc:
            sd['disc'] = self.disc
        if self.disctotal:
            sd['disctotal'] = self.disctotal
        if self.year:
            sd['year'] = self.year
        if self.encoder:
            sd['encoder'] = self.encoder
        if self.bpm:
            sd['bpm'] = self.bpm
        if self.comp:
            sd['compilaton'] = self.comp
        if self.grouping:
            sd['grouping'] = self.grouping
        if self.comments:
            sd['comments'] = self.comments
        if self.lyrics:
            sd['lyrics'] = self.lyrics
        if self.length:
            sd['length'] = self.length
        if self.bitrate:
            sd['bitrate'] = self.bitrate
        if self.samplerate:
            sd['samplerate'] = self.samplerate
        if self.channels:
            sd['channels'] = self.channels
        if self.bitdepth:
            sd['bitdepth'] = self.bitdepth
        if self.format:
            sd['format'] = self.format
        return sd


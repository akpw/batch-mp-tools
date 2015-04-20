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


import os
from string import Template
from batchmp.commons.descriptors import (
        PropertyDescriptor,
        LazyFunctionPropertyDescriptor,
        FunctionPropertyDescriptor,
        WeakMethodPropertyDescriptor)


# Tag Field Descriptors
class TaggableMediaFieldDescriptor(PropertyDescriptor):
    pass

class ExpandableMediaFieldDescriptor(TaggableMediaFieldDescriptor):
    def __set__(self, instance, value):
        if value:
            value = instance._process_value(value)
        super().__set__(instance, value)

class NullableMediaFieldDescriptor(PropertyDescriptor):
    def __set__(self, instance, value):
        if value is not None:
            if not isinstance(value, list):
                raise ValueError('{}: Nullable fields should be either None or a list of taggable fields'.format(value))
            taggable_fields = [field for field in instance.taggable_fields()]
            for field in value:
                if not field in taggable_fields:
                    raise ValueError('Field is not supported: {}'.format(field))
        super().__set__(instance, value)

class NonTaggableMediaFieldDescriptor(PropertyDescriptor):
    pass

# Art Field is a lazy property
class ArtFieldDescriptor(LazyFunctionPropertyDescriptor):
    pass

class TagHolder:
    ''' Tag Holder
            Defines supported tags & the protocol
            Supports tag templates processing
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

    # additional non-tag properties
    deferred_art_method = WeakMethodPropertyDescriptor()
    filepath = PropertyDescriptor()
    template_processor_method = FunctionPropertyDescriptor()
    nullable_fields = NullableMediaFieldDescriptor()

    def __init__(self, copy_empty_vals = False, nullable_fields = None,
                            copy_non_taggable = False, process_templates = True):
        self._copy_empty_vals = copy_empty_vals
        self._copy_non_taggable = copy_non_taggable
        self._process_templates = process_templates
        self.nullable_fields = nullable_fields

    @property
    def copy_empty_vals(self):
        return self._copy_empty_vals
    @property
    def copy_non_taggable(self):
        return self._copy_non_taggable
    @property
    def process_templates(self):
        return self._process_templates

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
        ''' generates names of non-writable tag fields
        '''
        for c in cls.__mro__:
            for field, descr in vars(c).items():
                if isinstance(descr, NonTaggableMediaFieldDescriptor):
                    yield field

    @classmethod
    def textual_fields(cls):
        for c in cls.__mro__:
            for field, descr in vars(c).items():
                if isinstance(descr, ExpandableMediaFieldDescriptor):
                    yield field

    @classmethod
    def fields(cls):
        ''' generates names of all tag fields
        '''
        yield from cls.taggable_fields
        yield from cls.non_taggable_fields

    def copy_tags(self, tag_holder = None):
        ''' Copies tags from passed tag_holder object
            Supports tag templates processing
        '''
        if not tag_holder:
            return

        fields = self.fields if tag_holder.copy_non_taggable else self.taggable_fields

        if tag_holder.template_processor_method:
            self.template_processor_method = tag_holder.template_processor_method

        for field in fields():
            value = getattr(tag_holder, field)
            if (value is not None) or \
                        (tag_holder.copy_empty_vals) or \
                            (tag_holder.nullable_fields and (field in tag_holder.nullable_fields)):
                setattr(self, field, value)

    def clear_tags(self, reset_art = False):
        ''' clears writable tags values
        '''
        for field in self.taggable_fields():
            setattr(self, field, None)
            if reset_art and hasattr(self, 'art'):
                del self.art

    def reset_tags(self):
        ''' resets a tag holder to its initial state
        '''
        self.template_processor_method = None
        self.filepath = None
        self.clear_tags(reset_art = True)

    # Internal Helpers
    def _process_value(self, value):
        ''' templates processing
        '''
        if not self.process_templates:
            return value

        if self.template_processor_method:
            return (self.template_processor_method(self._expand_templates(value)))
        else:
            return self._expand_templates(value)

    def _expand_templates(self, value):
        ''' expands template values
        '''
        template = Template(value)
        return template.safe_substitute(self._substitute_dictionary)

    @property
    def _substitute_dictionary(self):
        ''' internal property for template value substitution
        '''
        sd = {}
        sd['title'] = self.title if self.title else ''
        sd['album'] = self.album if self.album else ''
        sd['artist'] = self.artist if self.artist else ''
        sd['albumartist'] = self.albumartist if self.albumartist else ''
        sd['genre'] = self.genre if self.genre else ''
        sd['composer'] = self.composer if self.composer else ''
        sd['track'] = self.track if self.track else ''
        sd['tracktotal'] = self.tracktotal if self.tracktotal else ''
        sd['disc'] = self.disc if self.disc else ''
        sd['disctotal'] = self.disctotal if self.disctotal else ''
        sd['year'] = self.year if self.year else ''
        sd['encoder'] = self.encoder if self.encoder else ''
        sd['bpm'] = self.bpm if self.bpm else ''
        sd['compilaton'] = self.comp if self.comp else ''
        sd['grouping'] = self.grouping if self.grouping else ''
        sd['comments'] = self.comments if self.comments else ''
        sd['lyrics'] = self.lyrics if self.lyrics else ''
        sd['length'] = self.length if self.length else ''
        sd['bitrate'] = self.bitrate if self.bitrate else ''
        sd['samplerate'] = self.samplerate if self.samplerate else ''
        sd['channels'] = self.channels if self.channels else ''
        sd['bitdepth'] = self.bitdepth if self.bitdepth else ''
        sd['format'] = self.format if self.format else ''

        sd['filename'] = os.path.splitext(os.path.basename(self.filepath))[0] if self.filepath else ''

        return sd


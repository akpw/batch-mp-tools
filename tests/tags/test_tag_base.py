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
from batchmp.tags.handlers.tagsholder import TagHolder
from ..base import test_base


class TagsTest(test_base.BMPTest):
    @classmethod
    def setUpClass(cls):
        cls.src_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), 'data'))
        cls.bckp_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '.data'))

        super(TagsTest, cls).setUpClass()

        cls.test_tags_holder = TagTestsDataHolder(cls.src_dir)


class TagTestsDataHolder(TagHolder):
    def __init__(self, src_dir):
        super().__init__()
        self._png_art = None
        self._jpg_art = None
        self.src_dir = src_dir

        self.title = 'Test Title'
        self.album = 'Test Album'
        self.artist = 'Test Artist'
        self.albumartist = 'Test Album Artist'
        self.genre = 'Test Genre'
        self.composer  = 'Test Composer'
        self.track = 1
        self.tracktotal = 50
        self.disc = 1
        self.disctotal = 2
        self.year = 2015
        self.encoder = 'Test Encoder'
        self.art = self.jpg_art

        self.bpm = 6
        self.comp = True
        self.grouping = 'test group'
        self.comments = 'test comments'
        self.lyrics = 'test lyrics'

    def print_fields(self):
        print('Title: {}'.format(self.title))
        print('Album: {}'.format(self.album))
        print('Artist: {}'.format(self.artist))
        print('Album Artist: {}'.format(self.albumartist))
        print('Genre: {}'.format(self.genre))
        print('Composer: {}'.format(self.composer))
        print('Track: {}'.format(self.track))
        print('tracktotal: {}'.format(self.tracktotal))
        print('Disk: {}'.format(self.disc))
        print('Disktotal: {}'.format(self.disctotal))
        print('Year: {}'.format(self.year))
        print('Encoder: {}'.format(self.encoder))

        print('BPM: {}'.format(self.bpm))
        print('Compilation: {}'.format(self.comp))
        print('Grouping: {}'.format(self.grouping))
        print('Comments: {}'.format(self.comments))
        print('Lyrics: {}'.format(self.lyrics))

        print('Length: {}'.format(self.length))
        print('Bitrate: {}'.format(self.bitrate))
        print('Samplerate: {}'.format(self.samplerate))
        print('Channels: {}'.format(self.channels))
        print('Format: {}'.format(self.format))

        print ('Artwork exists' if self.has_artwork else 'No artwork')
        print('')

    @property
    def png_art(self):
        if not self._png_art:
            with open(os.path.join(self.src_dir, '00 art.png'), 'rb') as f:
                self._png_art = f.read()
        return self._png_art

    @property
    def jpg_art(self):
        if not self._jpg_art:
            with open(os.path.join(self.src_dir, '00 art.jpg'), 'rb') as f:
                self._jpg_art = f.read()
        return self._jpg_art

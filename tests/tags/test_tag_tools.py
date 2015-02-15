#!/usr/bin/env python
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

import os, sys, unittest
from batchmp.tags.handlers.basehandler import TagHandler, TagHolder
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from .test_tag_base import TagsTest

class TagsTests(TagsTest):
    def setUp(self):
        self.mfpathes = [os.path.join(self.src_dir, f) for f in os.listdir(self.src_dir)]
        self.hname = lambda h: 'MutagenTagHandler' if isinstance(h, MutagenTagHandler) else 'FFmpegTagHandler'

    # Tests
    def test_mthandler_fields(self):
        self._fields(MutagenTagHandler())

    def test_ffhandler_fields(self):
        self._fields(FFmpegTagHandler())

    def test_mthandler_set_tags(self):
        self._set_tags(MutagenTagHandler(), compare = True)

    def test_ffhandler_set_tags(self):
        self._set_tags(FFmpegTagHandler(), compare = False)

    def test_mthandler_remove_tags(self):
        self._remove_tags(MutagenTagHandler())

    def test_ffhandler_remove_tags(self):
        self._remove_tags(FFmpegTagHandler())


    # Helper methods
    def _fields(self, handler):
        for f in self.mfpathes:
            if handler.can_handle(f):
                for field in TagHandler.fields():
                    self.assertTrue(hasattr(handler, field),
                        msg = '\n{2}: the field "{0}" in <{1}> is not in fields'.format
                                                (field, os.path.basename(f), self.hname(handler)))

                for field in TagHandler.readable_fields():
                    self.assertTrue(hasattr(handler, field),
                        msg = '\n{2}: the field "{0}" in <{1}> is not in readable fields'.format
                                                (field, os.path.basename(f), self.hname(handler)))

    def _set_tags(self, handler, compare = True):
        mfpathes = [os.path.join(self.src_dir, f) for f in os.listdir(self.src_dir)]

        # set tags from test data
        for f in self.mfpathes:
            if handler.can_handle(f):
                handler.copy_fields(self.test_tags_holder)
                handler.save()

        # read & compare tag values
        self._read_and_compare(handler, self.test_tags_holder, compare = compare)

        # restore original state if needed
        self.resetDataFromBackup(quiet=True)

    def _remove_tags(self, handler):
        for f in self.mfpathes:
            if handler.can_handle(f):
                handler.remove_tags()
                handler.save()

        # read & compare tag values
        self._read_and_compare(handler, TagHolder())

        # restore original state if needed
        self.resetDataFromBackup(quiet=True)

    def _read_and_compare(self, handler, holder, compare = True):
        # read tags and compare to test data
        for f in self.mfpathes:
            if handler.can_handle(f):
                for field in handler.fields():
                    tag_value = getattr(handler, field)
                    test_data = getattr(holder, field)
                    if compare:
                        self.assertEqual(tag_value, test_data,
                            msg = '\n{2}: the field "{0}" in <{1}> did not pass set & compare'.format
                                                 (field, os.path.basename(f), self.hname(handler)))



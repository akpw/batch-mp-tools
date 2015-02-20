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

import os, sys, unittest, weakref, gc
from batchmp.tags.handlers.basehandler import TagHandler
from batchmp.tags.handlers.tagsholder import TagHolder
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from .test_tag_base import TagsTest

class TagsTests(TagsTest):
    def setUp(self):
        self.mfpathes = [os.path.join(self.src_dir, f) for f in os.listdir(self.src_dir)]
        self.hname = lambda h: 'MutagenTagHandler' if isinstance(h, MutagenTagHandler) else 'FFmpegTagHandler'

    # Tests
    def test_mthandler_base(self):
        handler = MutagenTagHandler()
        handler.copy_tags(self.test_tags_holder)
        self.assertIsNotNone(handler.tag_holder.art)

        r = weakref.ref(handler)
        del handler
        gc.collect()
        self.assertIsNone(r())

    def test_ffhandler_base(self):
        handler = FFmpegTagHandler()
        handler.copy_tags(self.test_tags_holder)
        self.assertIsNotNone(handler.tag_holder.art)

        r = weakref.ref(handler)
        del handler
        gc.collect()
        self.assertIsNone(r())

    def test_tag_handlers_chain(self):
        handler = MutagenTagHandler()
        self.assertFalse(handler.can_handle(os.path.join(self.src_dir, 'background noise.flv')))

        handler = MutagenTagHandler() + FFmpegTagHandler()
        self.assertTrue(handler.can_handle(os.path.join(self.src_dir, 'background noise.flv')))

        r = weakref.ref(handler)
        del handler
        gc.collect()
        self.assertIsNone(r())

    def test_mthandler_fields(self):
        self._fields_check(MutagenTagHandler())

    def test_ffhandler_fields(self):
        self._fields_check(FFmpegTagHandler())

    def test_mthandler_set_tags(self):
        self._set_tags_check(MutagenTagHandler(), compare = True)

    def test_ffhandler_set_tags(self):
        self._set_tags_check(FFmpegTagHandler(), compare = False)

    def test_mthandler_remove_tags(self):
        self._remove_tags_check(MutagenTagHandler())

    def test_ffhandler_remove_tags(self):
        self._remove_tags_check(FFmpegTagHandler())


    # Helper methods
    def _fields_check(self, handler):
        for f in self.mfpathes:
            if handler.can_handle(f):
                for field in handler.tag_holder.taggable_fields():
                    self.assertTrue(hasattr(handler.tag_holder, field),
                        msg = '\n{2}: the field "{0}" in <{1}> is not in taggable fields'.format
                                                (field, os.path.basename(f), self.hname(handler)))

                for field in handler.tag_holder.non_taggable_fields():
                    self.assertTrue(hasattr(handler.tag_holder, field),
                        msg = '\n{2}: the field "{0}" in <{1}> is not in non-taggable fields'.format
                                                (field, os.path.basename(f), self.hname(handler)))

    def _set_tags_check(self, handler, compare = True):
        mfpathes = [os.path.join(self.src_dir, f) for f in os.listdir(self.src_dir)]

        # set tags from test data
        for f in self.mfpathes:
            if handler.can_handle(f):
                handler.copy_tags(self.test_tags_holder)
                handler.save()

        # read & compare tag values
        self._read_and_compare_check(handler, self.test_tags_holder, compare = compare)

        # restore original state if needed
        self.resetDataFromBackup(quiet=True)

    def _remove_tags_check(self, handler):
        for f in self.mfpathes:
            if handler.can_handle(f):
                handler.clear_tags()
                handler.save()

        # read & compare tag values
        self._read_and_compare_check(handler, TagHolder())

        # restore original state if needed
        self.resetDataFromBackup(quiet=True)

    def _read_and_compare_check(self, handler, holder, compare = True):
        # read tags and compare to test data
        for f in self.mfpathes:
            if handler.can_handle(f):
                for field in handler.tag_holder.taggable_fields():
                    tag_value = getattr(handler.tag_holder, field)
                    test_data = getattr(holder, field)
                    if compare:
                        self.assertEqual(tag_value, test_data,
                            msg = '\n{2}: the field "{0}" in <{1}> did not pass set & compare'.format
                                                 (field, os.path.basename(f), self.hname(handler)))



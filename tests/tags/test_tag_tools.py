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
from batchmp.tags.processors.basetp import BaseTagProcessor
from batchmp.fstools.builders.fsprms import FSEntryParamsExt
from .test_tag_base import TagsTest

class TagsTests(TagsTest):
    def setUp(self):
        self.mfpathes = [os.path.join(self.src_dir, f) for f in os.listdir(self.src_dir)]
        self.hname = lambda handler: 'MutagenTagHandler' if isinstance(handler.responder, MutagenTagHandler) else 'FFmpegTagHandler'

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
        self.assertFalse(handler.can_handle(os.path.join(self.src_dir, '04 background noise.flv')))

        handler = MutagenTagHandler() + FFmpegTagHandler()
        self.assertTrue(handler.can_handle(os.path.join(self.src_dir, '04 background noise.flv')))

        r = weakref.ref(handler)
        del handler
        gc.collect()
        self.assertIsNone(r())

    def test_mthandler_fields(self):
        self._fields_check(MutagenTagHandler())

    def test_ffhandler_fields(self):
        ## python -m unittest tests.tags.test_tag_tools.TagsTests.test_ffhandler_fields
        self._fields_check(FFmpegTagHandler())

    def test_set_tags(self):
        # test setting tags from test data
        fs_entry_params = FSEntryParamsExt()
        fs_entry_params.src_dir = self.src_dir
        fs_entry_params.quiet = True
        BaseTagProcessor().set_tags_visual(fs_entry_params,
                                            tag_holder = self.test_tags_holder)
        handler = MutagenTagHandler() + FFmpegTagHandler()
        for mfpath in self.mfpathes:
            if handler.can_handle(mfpath):
                compare = True if isinstance(handler.responder, MutagenTagHandler) else False
                self._read_and_compare(mfpath, self.test_tags_holder, compare = compare)

        #restore original state if needed
        self.resetDataFromBackup(quiet=True)

    def test_remove_tags(self):
        # test removing tags
        fs_entry_params = FSEntryParamsExt()
        fs_entry_params.src_dir = self.src_dir
        fs_entry_params.quiet = True
        BaseTagProcessor().set_tags_visual(fs_entry_params,
                                            tag_holder = self.test_tags_holder)
        BaseTagProcessor().remove_tags(fs_entry_params)

        handler = MutagenTagHandler() + FFmpegTagHandler()
        tag_holder =  TagHolder()
        for mfpath in self.mfpathes:
            if handler.can_handle(mfpath):
                self._read_and_compare(mfpath, tag_holder)

        #restore original state if needed
        self.resetDataFromBackup(quiet=True)

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


    def _read_and_compare(self, mfpath, holder, compare = True):
        # read tags and compare to test data
        handler = MutagenTagHandler() + FFmpegTagHandler()
        if handler.can_handle(mfpath):
            for field in handler.tag_holder.taggable_fields():
                tag_value = getattr(handler.tag_holder, field)
                test_data = getattr(holder, field)
                if compare:
                    self.assertEqual(tag_value, test_data,
                        msg = '\n{2}: the field "{0}" in <{1}> did not pass set & compare'.format
                                             (field, os.path.basename(mfpath), self.hname(handler)))



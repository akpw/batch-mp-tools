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


import unittest, os, inspect, sys, math
import shutil, datetime
from batchmp.ffmptools.ffutils import FFH
from batchmp.fstools.fsutils import FSH

from .test_ffmp_base import FFMPTest
from scripts.bmfp import BMFPArgParser
from batchmp.ffmptools.ffcommands.denoise import Denoiser
from batchmp.ffmptools.ffcommands.convert import Convertor
from batchmp.ffmptools.ffcommands.fragment import Fragmenter
from batchmp.ffmptools.ffcommands.segment import Segmenter

class FFMPTests(FFMPTest):
    def setUp(self):
        super(FFMPTests, self).setUp()

    def tearDown(self):
        # cleanup
        self.resetDataFromBackup(quiet=True)

    def test_apply_af_filters_changes(self):
        print('Applying audio filters, might take a while ...')
        media_files = [f for f in FFH.media_files(src_dir = self.src_dir, exclude = 'bmfp*')]
        self.assertNotEqual(media_files, [], msg = 'No media files selected')

        # get the original media files md5 hashes
        orig_hashes = {fname: FSH.file_md5(fname, hex=True) for fname in media_files}

        hpass, lpass, num_passes = 200, 0, 4
        Denoiser().apply_af_filters(self.src_dir, exclude = 'bmfp*',
                                    highpass=hpass, lowpass=lpass, num_passes=num_passes)

        # check that the original files were replaced with their denoised versions
        denoised_hashes = {fname: FSH.file_md5(fname, hex=True) for fname in media_files}
        for hash_key in orig_hashes.keys():
            self.assertNotEqual(orig_hashes[hash_key], denoised_hashes[hash_key])

    def test_apply_af_filters_audio(self):
        print('Applying audio filters on audio files')

        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')


        hpass, lpass, num_passes = 200, 0, 4
        Denoiser().apply_af_filters(self.src_dir, include = 'bmfp_a',   filter_files = False,
                                    highpass=hpass, lowpass=lpass, num_passes=num_passes,
                                    preserve_metadata = True, ffmpeg_options = ' -vn')

        processed_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')

        for orig_entry, processed_entry in zip(orig_media_entries, processed_media_entries):
            self.compare_media(orig_entry, processed_entry, strict_compare = True)

    def test_apply_af_filters_video(self):
        print('Applying audio filters on video files')

        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        hpass, lpass, num_passes = 200, 0, 4
        Denoiser().apply_af_filters(self.src_dir, include = 'bmfp_v',   filter_files = False,
                                    highpass=hpass, lowpass=lpass, num_passes=num_passes,
                                    preserve_metadata = True, ffmpeg_options = None)

        processed_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')

        for orig_entry, processed_entry in zip(orig_media_entries, processed_media_entries):
            self.compare_media(orig_entry, processed_entry, strict_compare = True)

    def test_convert_audio(self):
        print('Converting audio')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Convertor().convert(self.src_dir, include = 'bmfp_a',  filter_files = False,
                            target_format = 'mp3', convert_options = BMFPArgParser.DEFAULT_CONVERSION_OPTIONS,
                            preserve_metadata = True)

        processed_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')

        print('Comparing media entries...')
        for orig_entry, processed_entry in zip(orig_media_entries, processed_media_entries):
            self.compare_media(orig_entry, processed_entry)

    def test_convert_video(self):
        print('Converting video')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Convertor().convert(self.src_dir, include = 'bmfp_v',  filter_files = False,
                            target_format = 'mp4', convert_options = BMFPArgParser.DEFAULT_CONVERSION_OPTIONS,
                            preserve_metadata = True)

        processed_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')

        print('Comparing media entries...')
        for orig_entry, processed_entry in zip(orig_media_entries, processed_media_entries):
            self.compare_media(orig_entry, processed_entry)


    def test_fragment_audio(self):
        print('Fragmenting audio')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Fragmenter().fragment(self.src_dir, include = 'bmfp_a', filter_files = False,
                                fragment_starttime = 0, fragment_duration = 1,
                                serial_exec = False,
                                preserve_metadata = True, ffmpeg_options = ' -vn')

        processed_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')

        for orig_entry, processed_entry in zip(orig_media_entries, processed_media_entries):
            self.compare_media(orig_entry, processed_entry)


    def test_fragment_video(self):
        print('Fragmenting video')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Fragmenter().fragment(self.src_dir, include = 'bmfp_v', filter_files = False,
                              fragment_starttime = 0, fragment_duration = 1,
                              serial_exec = False, preserve_metadata = True)

        processed_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')

        for orig_entry, processed_entry in zip(orig_media_entries, processed_media_entries):
            self.compare_media(orig_entry, processed_entry)


    def test_segment_audio(self):
        print('Segmenting audio to parts of 1 sec')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Segmenter().segment(self.src_dir, include = 'bmfp_a', filter_files = False,
                                segment_size_MB = 0.0, segment_length_secs = 1,
                                serial_exec = False,
                                preserve_metadata = True, ffmpeg_options = ' -vn')

        src_dir = self.src_dir + '/bmfp_a'
        processed_media_entries = self._media_entries(src_dir, end_level = 0, include = '*_0.*')
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')

        for orig_entry, processed_entry in zip(orig_media_entries, processed_media_entries):
            self.compare_media(orig_entry, processed_entry)


    def test_segment_video(self):
        print('Segmenting video to parts of 50KB')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Segmenter().segment(self.src_dir, include = 'bmfp_v', filter_files = False,
                              segment_size_MB = 0.05, segment_length_secs = 0.0,
                              serial_exec = False, preserve_metadata = True)

        src_dir = self.src_dir + '/bmfp_v'
        processed_media_entries = self._media_entries(src_dir, end_level = 0, include = '*_0.*')
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')

        for orig_entry, processed_entry in zip(orig_media_entries, processed_media_entries):
            self.compare_media(orig_entry, processed_entry)


    # Internal helpers
    def _media_entries(self, src_dir = None, include = '*', exclude = '',
                       filter_files = True, filter_dirs = True, end_level = sys.maxsize):
        if not src_dir:
            src_dir = self.src_dir
        media_files = [fpath for fpath in FFH.media_files(src_dir, end_level = end_level,
                                                          include = include, filter_files = filter_files,
                                                          filter_dirs = filter_dirs)]
        media_entries = [FFH.media_file_info_full(fpath) for fpath in media_files]

        return media_entries




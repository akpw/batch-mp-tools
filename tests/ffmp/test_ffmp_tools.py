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


import unittest, os, sys
from .test_ffmp_base import FFMPTest
from batchmp.ffmptools.ffutils import FFH
from batchmp.fstools.fsutils import FSH
from batchmp.ffmptools.ffrunner import LogLevel
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands, FFmpegBitMaskOptions
from batchmp.ffmptools.ffcommands.denoise import Denoiser
from batchmp.ffmptools.ffcommands.normalize_peak import PeakNormalizer
from batchmp.ffmptools.ffcommands.convert import Convertor
from batchmp.ffmptools.ffcommands.fragment import Fragmenter
from batchmp.ffmptools.ffcommands.segment import Segmenter
from batchmp.ffmptools.ffcommands.silencesplit import SilenceSplitter
from batchmp.ffmptools.ffcommands.cuesplit import CueSplitter
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.mtghandler import MutagenTagHandler

class FFMPTests(FFMPTest):
    def setUp(self):
        super(FFMPTests, self).setUp()
        self.serial_exec_mode = True if os.name == 'nt' else False
        self.target_dir = os.path.join(self.src_dir, 'xResults')
        if not os.path.exists(self.target_dir):
            os.mkdir(self.target_dir)

    def tearDown(self):
        # cleanup
        self.resetDataFromBackup(quiet=True)

    def test_apply_af_filters_changes(self):
        #return ##
        print('Applying audio filters, might take a while ...')
        media_files = [f for f in FFH.media_files(src_dir = self.src_dir, exclude = 'bmfp*')]
        self.assertNotEqual(media_files, [], msg = 'No media files selected')

        # get the original media files md5 hashes
        orig_hashes = {os.path.basename(fname): FSH.file_md5(fname, hex=True) for fname in media_files}

        hpass, lpass, num_passes = 200, 3000, 3
        Denoiser().apply_af_filters(self.src_dir, exclude = 'bmfp*',
                                    highpass=hpass, lowpass=lpass, num_passes=num_passes,
                                    preserve_metadata = True,
                                    serial_exec = self.serial_exec_mode, target_dir = self.target_dir)

        # check that the original files differ from their denoised versions
        media_files = [f for f in FFH.media_files(src_dir = self.target_dir)]
        self.assertNotEqual(media_files, [], msg = 'No media files selected')

        denoised_hashes = {os.path.basename(fname): FSH.file_md5(fname, hex=True) for fname in media_files}
        for hash_key in orig_hashes.keys():
            self.assertNotEqual(orig_hashes[hash_key], denoised_hashes[hash_key])

    def test_apply_af_filters_audio(self):
        #return ##
        print('Applying audio filters on audio files')

        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        hpass, lpass, num_passes = 200, 3000, 4
        Denoiser().apply_af_filters(self.src_dir,
                                    include = 'bmfp_a', filter_files = False,
                                    highpass=hpass, lowpass=lpass, num_passes=num_passes,
                                    serial_exec = self.serial_exec_mode,
                                    preserve_metadata = True,
                                    target_dir = self.target_dir)

        processed_media_entries = self._media_entries(src_dir = self.target_dir)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_apply_af_filters_video(self):
        #return ##
        print('Applying audio filters on video files')

        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        hpass, lpass, num_passes = 200, 0, 4
        Denoiser().apply_af_filters(self.src_dir, include = 'bmfp_v',   filter_files = False,
                                    highpass=hpass, lowpass=lpass, num_passes=num_passes,
                                    serial_exec = self.serial_exec_mode,
                                    preserve_metadata = True,
                                    target_dir = self.target_dir)

        processed_media_entries = self._media_entries(src_dir = self.target_dir)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_convert_audio(self):
        #return ##
        print('Converting audio')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Convertor().convert(self.src_dir, include = 'bmfp_a',  filter_files = False,
                            target_format = 'mp3',
                            serial_exec = self.serial_exec_mode,
                            preserve_metadata = True,
                            target_dir = self.target_dir)

        processed_media_entries = self._media_entries(src_dir = self.target_dir)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_convert_video(self):
        #return ##
        print('Converting video')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Convertor().convert(self.src_dir, include = 'bmfp_v',  filter_files = False,
                            target_format = 'mp4',
                            serial_exec = self.serial_exec_mode,
                            preserve_metadata = True,
                            target_dir = self.target_dir)

        processed_media_entries = self._media_entries(src_dir = self.target_dir)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_fragment_audio(self):
        #return ##
        print('Fragmenting audio')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Fragmenter().fragment(self.src_dir, include = 'bmfp_a', filter_files = False,
                                fragment_starttime = 0, fragment_duration = 1,
                                serial_exec = self.serial_exec_mode,
                                preserve_metadata = True,
                                target_dir = self.target_dir)

        processed_media_entries = self._media_entries(src_dir = self.target_dir)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_fragment_video(self):
        #return ##
        print('Fragmenting video')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Fragmenter().fragment(self.src_dir, include = 'bmfp_v', filter_files = False,
                              fragment_starttime = 0, fragment_duration = 45,
                              serial_exec = self.serial_exec_mode,
                              preserve_metadata = True,
                              target_dir = self.target_dir)

        processed_media_entries = self._media_entries(src_dir = self.target_dir)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_segment_audio(self):
        #return ##
        print('Segmenting audio to parts of 1 sec')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Segmenter().segment(self.src_dir, include = 'bmfp_a', filter_files = False,
                                segment_size_MB = 0.0, segment_length_secs = 1,
                                serial_exec = self.serial_exec_mode,
                                preserve_metadata = True,
                                target_dir = self.target_dir)

        processed_media_entries = self._media_entries(src_dir = self.target_dir,
                                                      include = '*_0.*', filter_dirs = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_segment_video(self):
        #return ##
        print('Segmenting video to parts of 50KB')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Segmenter().segment(self.src_dir, include = 'bmfp_v', filter_files = False,
                              segment_size_MB = 0.05, segment_length_secs = 0.0,
                              serial_exec = self.serial_exec_mode,
                              preserve_metadata = True,
                              target_dir = self.target_dir)

        processed_media_entries = self._media_entries(src_dir = self.target_dir,
                                                      include = '*_0.*;*_00.*',
                                                      filter_dirs = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)


    def test_silencesplit_audio(self):
        #return ##
        print('Splitting audio on silence')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_a',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        SilenceSplitter().silence_split(self.src_dir,
                                include = 'bmfp_a', filter_files = False,
                                serial_exec = self.serial_exec_mode,
                                preserve_metadata = True,
                                target_dir = self.target_dir,
                                silence_min_duration = 0.1, silence_noise_tolerance_amplitude_ratio = 0.5)

        processed_media_entries = self._media_entries(src_dir = self.target_dir,
                                                      include = '*_0.*', filter_dirs = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_silencesplit_video(self):
        #return ##
        print('Splitting video on silence')
        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp_v',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        SilenceSplitter().silence_split(self.src_dir,
                                include = 'bmfp_v', filter_files = False,
                                serial_exec = self.serial_exec_mode,
                                preserve_metadata = True,
                                target_dir = self.target_dir,
                                silence_min_duration = 0.1, silence_noise_tolerance_amplitude_ratio = 0.5)

        processed_media_entries = self._media_entries(src_dir = self.target_dir,
                                                      include = '*_0.*',
                                                      filter_dirs = False)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_cuesplit_audio(self):
        #return ##
        print('Cue splitting')
        CueSplitter().cue_split(self.src_dir, include = 'bmfp_a',  filter_files = False,
                serial_exec = self.serial_exec_mode,
                preserve_metadata = True,
                target_dir = self.target_dir,
                target_format = 'mp4')

        media_files = [fpath for fpath in FFH.media_files(src_dir = self.target_dir)]
        self.assertEqual(len(media_files), 18)

        handler = MutagenTagHandler() + FFmpegTagHandler()
        for media_file in media_files:
            if handler.can_handle(media_file):
                self.assertEqual(handler.tag_holder.album, 'BMFP NOISE PRODUCTION AUDIO')
                self.assertEqual(handler.tag_holder.albumartist, 'BMFP TESTER')
                self.assertEqual(handler.tag_holder.year, 2016)
                self.assertEqual(handler.tag_holder.genre, 'NOISY CLASSICAL')


    def test_peak_normalize(self):
        #return ##
        print('Normalizing media files')

        orig_media_entries = self._media_entries(end_level = 1, include = 'bmfp*',  filter_files = False)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        PeakNormalizer().peak_normalize(self.src_dir,
                                    include = 'bmfp*', filter_files = False,
                                    serial_exec = self.serial_exec_mode,
                                    preserve_metadata = True, log_level = LogLevel.QUIET,
                                    target_dir = self.target_dir)

        processed_media_entries = self._media_entries(src_dir = self.target_dir)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)


    # Internal helpers
    def _media_entries(self, src_dir = None, include = None, exclude = None,
                       filter_files = True, filter_dirs = True, end_level = sys.maxsize):
        if src_dir is None:
            src_dir = self.src_dir
        media_files = [fpath for fpath in FFH.media_files(src_dir, end_level = end_level,
                                                          include = include, filter_files = filter_files,
                                                          filter_dirs = filter_dirs)]
        #for fpath in media_files:
        #    print(os.path.basename(fpath))

        media_entries = [FFH.media_file_info_full(fpath) for fpath in media_files]

        return media_entries

    def _check_media_entries(self, orig_media_entries, processed_media_entries):
        print('Comparing media entries...')
        self.assertEqual(len(orig_media_entries), len(processed_media_entries),
                          msg = '\n\tDifferent number of media entries:'
                                '\n\twas {0} originals, but {1} processed'.format(
                                len(orig_media_entries), len(processed_media_entries)))

        for orig_entry, processed_entry in zip(orig_media_entries, processed_media_entries):
            self.compare_media(orig_entry, processed_entry, strict_compare = True)



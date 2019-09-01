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
from batchmp.ffmptools.processors.ffentry import FFEntryParams, FFEntryParamsExt
from batchmp.ffmptools.ffrunner import LogLevel
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegBitMaskOptions


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
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_apply_af_filters_changes
        ff_entry_params = self._ff_entry(exclude = 'bmfp*', general_options = FFmpegBitMaskOptions.MUXING_QUEUE_SIZE, end_level = 10)

        media_files = [f for f in FFH.media_files(ff_entry_params)]
        self.assertNotEqual(media_files, [], msg = 'No media files selected')

        # get the original media files md5 hashes
        orig_hashes = {os.path.basename(fname): FSH.file_md5(fname, hex=True) for fname in media_files}

        print('Applying audio filters, might take a while ...')        
        hpass, lpass, num_passes = 200, 3000, 3
        Denoiser().apply_af_filters(ff_entry_params,
                                    highpass=hpass, lowpass=lpass, num_passes=num_passes)

        # check that the original files differ from their denoised versions
        media_files = [f for f in FFH.media_files(ff_entry_params)]
        self.assertNotEqual(media_files, [], msg = 'No media files selected')

        denoised_hashes = {os.path.basename(fname): FSH.file_md5(fname, hex=True) for fname in media_files}
        counter = 0
        for hash_key in orig_hashes.keys():
            if orig_hashes[hash_key] == denoised_hashes[hash_key]:
                counter += 1
        self.assertTrue(counter == 0, msg = '{} files not processed'.format(counter))

    def test_apply_af_filters_audio(self):        
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_apply_af_filters_audio
        ff_entry_params = self._ff_entry(include = 'bmfp_a')

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Applying audio filters on audio files')
        hpass, lpass, num_passes = 200, 3000, 4
        Denoiser().apply_af_filters(ff_entry_params, highpass=hpass, lowpass=lpass, num_passes=num_passes)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_apply_af_filters_video(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_apply_af_filters_video
        ff_entry_params = self._ff_entry(include = 'bmfp_v', general_options = FFmpegBitMaskOptions.MUXING_QUEUE_SIZE)

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Applying audio filters on video files')
        hpass, lpass, num_passes = 200, 0, 4
        Denoiser().apply_af_filters(ff_entry_params, highpass=hpass, lowpass=lpass, num_passes=num_passes)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_convert_audio(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_convert_audio
        ff_entry_params = self._ff_entry(include = 'bmfp_a')
        ff_entry_params.target_format = '.mp3'

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Converting audio')
        Convertor().convert(ff_entry_params)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir        
        
        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_convert_video(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_convert_video
        ff_entry_params = self._ff_entry(include = 'bmfp_v')
        ff_entry_params.target_format = '.mp4'

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Converting video')
        Convertor().convert(ff_entry_params)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir        

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_fragment_audio(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_fragment_audio
        ff_entry_params = self._ff_entry(include = 'bmfp_a')
        ff_entry_params.target_format = '.mp3'

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Fragmenting audio')
        Fragmenter().fragment(ff_entry_params, fragment_starttime = 0, fragment_duration = 1)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir        

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_fragment_video(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_fragment_video
        ff_entry_params = self._ff_entry(include = 'bmfp_v')
        ff_entry_params.target_format = '.mp4'

        print('Fragmenting video')
        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        Fragmenter().fragment(ff_entry_params, fragment_starttime = 0, fragment_duration = 45)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir        

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_segment_audio(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_segment_audio
        ff_entry_params = self._ff_entry(include = 'bmfp_a')

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Segmenting audio to parts of 1 sec')
        Segmenter().segment(ff_entry_params, segment_size_MB = 0.0, segment_length_secs = 1)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir       
        ff_entry_params.include = '*_0.*'
        ff_entry_params.filter_dirs = False

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_segment_video(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_segment_video
        ff_entry_params = self._ff_entry(include = 'bmfp_v')

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Segmenting video to parts of 50KB')
        Segmenter().segment(ff_entry_params, segment_size_MB = 0.05, segment_length_secs = 0.0)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir       
        ff_entry_params.include = include = '*_0.*;*_00.*'
        ff_entry_params.filter_dirs = False

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)


    def test_silencesplit_audio(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_silencesplit_audio
        ff_entry_params = self._ff_entry(include = 'bmfp_a')

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Splitting audio on silence')
        SilenceSplitter().silence_split(ff_entry_params,
                                silence_min_duration = 0.1, silence_noise_tolerance_amplitude_ratio = 0.5)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir      
        ff_entry_params.include = '*_0.*' 
        ff_entry_params.filter_dirs = False

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_silencesplit_video(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_silencesplit_video
        ff_entry_params = self._ff_entry(include = 'bmfp_v')

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Splitting video on silence')
        SilenceSplitter().silence_split(ff_entry_params,
                                silence_min_duration = 0.1, silence_noise_tolerance_amplitude_ratio = 0.5)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir      
        ff_entry_params.include = '*_0.*' 
        ff_entry_params.filter_dirs = False

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)

    def test_cuesplit_audio(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_cuesplit_audio
        ff_entry_params = self._ff_entry(include = 'bmfp_a')
        ff_entry_params.target_format = '.mp4'

        print('Cue splitting')
        CueSplitter().cue_split(ff_entry_params)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir      


        media_files = [fpath for fpath in FFH.media_files(ff_entry_params)]
        self.assertEqual(len(media_files), 18)

        handler = MutagenTagHandler() + FFmpegTagHandler()
        for media_file in media_files:
            if handler.can_handle(media_file):
                self.assertEqual(handler.tag_holder.album, 'BMFP NOISE PRODUCTION AUDIO')
                self.assertEqual(handler.tag_holder.albumartist, 'BMFP TESTER')
                self.assertEqual(handler.tag_holder.year, 2016)
                self.assertEqual(handler.tag_holder.genre, 'NOISY CLASSICAL')


    def test_peak_normalize(self):
        ## python -m unittest tests.ffmp.test_ffmp_tools.FFMPTests.test_peak_normalize
        ff_entry_params = self._ff_entry(include = 'bmfp*')

        orig_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(orig_media_entries, [], msg = 'No media files selected')

        print('Normalizing media files')
        PeakNormalizer().peak_normalize(ff_entry_params)

        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.target_dir      

        processed_media_entries = self._media_entries(ff_entry_params)
        self.assertNotEqual(processed_media_entries, [], msg = 'No media files selected')
        self._check_media_entries(orig_media_entries, processed_media_entries)


    # Internal helpers
    def _media_entries(self, ff_entry_params):
        if ff_entry_params.src_dir is None:
            ff_entry_params.src_dir = self.src_dir
        media_files = [fpath for fpath in FFH.media_files(ff_entry_params)]

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

    def _ff_entry(self, include = None, exclude = None, general_options = None, end_level = 1, log = False):
        ff_entry_params = FFEntryParamsExt()
        ff_entry_params.src_dir = self.src_dir
        ff_entry_params.target_dir = self.target_dir
        ff_entry_params.filter_files = False
        ff_entry_params.end_level = end_level
        ff_entry_params.serial_exec = self.serial_exec_mode
        ff_entry_params.include_dirs = True

        if include:
            ff_entry_params.include = include        
        if exclude:
            ff_entry_params.exclude = exclude
        if general_options:
            ff_entry_params.ff_general_options |= general_options
        if log:
            ff_entry_params.log_level = LogLevel.VERBOSE

        return ff_entry_params

    def _print_entry(self, entry):
        print (', '.join("%s: %s" % item for item in vars(entry).items()))        
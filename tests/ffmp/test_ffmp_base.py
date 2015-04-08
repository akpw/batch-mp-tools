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
from ..base import test_base
from batchmp.ffmptools.ffutils import FFH

class FFMPTest(test_base.BMPTest):
    @classmethod
    def setUpClass(cls):
        cls.src_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), 'data'))
        cls.bckp_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '.data'))
        super(FFMPTest, cls).setUpClass()

    def compare_media(self, full_entry_orig, full_entry_processed, strict_compare = True):
        ''' Compares base stream info for two media files
        '''
        self.assertIsNotNone(full_entry_orig,
                        msg = 'Original media info should not be None')
        self.assertIsNotNone(full_entry_processed,
                        msg = 'Processed media info should not be None')
        self.assertIsNotNone(full_entry_orig.audio_streams,
                        msg = '{}: Original media audio streams should not be None'.format(full_entry_orig.path))
        self.assertIsNotNone(full_entry_processed.audio_streams,
                        msg = '{}: Processed media audio streams should not be None'.format(full_entry_processed.path))

        assert_method = self.assertEqual if strict_compare else self.assertLessEqual

        # Check audio streams
        assert_method(len(full_entry_orig.audio_streams), len(full_entry_processed.audio_streams),
                        msg = '\n{0}\n{1}'
                                    '\n\tDifferent number of audio streams:'
                                    '\n\tOriginal has {2}, but processed has {3}'.format(
                                full_entry_orig.path, full_entry_processed.path,
                                len(full_entry_orig.audio_streams), len(full_entry_processed.audio_streams)))

        # Check video streams
        assert_method(len(full_entry_orig.video_streams), len(full_entry_processed.video_streams),
                        msg = '\n{0}\n{1}'
                                    '\n\tDifferent number of video streams:'
                                    '\n\tOriginal has {2}, but processed has {3}'.format(
                                full_entry_orig.path, full_entry_processed.path,
                                len(full_entry_orig.video_streams), len(full_entry_processed.video_streams)))

        # Check artwork streams
        assert_method(len(full_entry_orig.artwork_streams), len(full_entry_processed.artwork_streams),
                        msg = '\n{0}\n{1}'
                                    '\n\tDifferent number of artwork streams:'
                                    '\n\tOriginal has {2}, but processed has {3}'.format(
                                full_entry_orig.path, full_entry_processed.path,
                                len(full_entry_orig.artwork_streams), len(full_entry_processed.artwork_streams)))








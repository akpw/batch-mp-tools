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
import batchmp.ffmptools.ffutils as ffutils
from batchmp.fstools.fsutils import FSH

from .test_ffmp_base import FFMPTest
from batchmp.ffmptools.ffcommands.denoise import Denoiser

class FFMPTests(FFMPTest):
    def setUp(self):
        super(FFMPTests, self).setUp()

    def test_apply_af_filters(self):
        print('Now testing applying filters, might take a while...')
        media_files = [f for f in ffutils.FFH.media_files(src_dir = self.src_dir)]

        # get the original media files md5 hashes
        orig_hashes = {fname: FSH.file_md5(fname, hex=True) for fname in media_files}

        hpass, lpass, num_passes = 200, 0, 4
        Denoiser().apply_af_filters(self.src_dir, highpass=hpass, lowpass=lpass, num_passes=num_passes)

        # check that the original files were replaced with their denoised versions
        denoised_hashes = {fname: FSH.file_md5(fname, hex=True) for fname in media_files}
        for hash_key in orig_hashes.keys():
            self.assertNotEqual(orig_hashes[hash_key], denoised_hashes[hash_key])

        # cleanup
        self.resetDataFromBackup(quiet=True)



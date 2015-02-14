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
import batchmp.ffmptools.ffmputils as ffutils
from batchmp.fstools.fsutils import FSH

from .test_ffmp_base import FFMPTest
from batchmp.ffmptools.ffmp import FFMP

class FFMPTests(FFMPTest):
    def setUp(self):
        super(FFMPTests, self).setUp()
        self.ffmp = FFMP(self.src_dir)

    def test_apply_af_filters_raise(self):
        self.assertRaises(ffutils.FFmpegArgsError, self.ffmp.apply_af_filters)

    def test_apply_af_filters(self):
        print('Now testing applying filters, might take a while...')
        media_files = ffutils.get_media_files(src_dir = self.src_dir, recursive = True)

        # get the original media files md5 hashes
        orig_hashes = {fname: FSH.file_md5(fname, hex=True) for fname in media_files}

        hpass, lpass, num_passes, recursive, quiet = 200, 0, 4, True, False
        cpu_core_time, total_elapsed = self.ffmp.apply_af_filters(
                                                highpass=hpass,
                                                lowpass=lpass,
                                                num_passes=num_passes,
                                                recursive = recursive,
                                                quiet=quiet)
        ttd = datetime.timedelta(seconds = math.ceil(total_elapsed))
        ctd = datetime.timedelta(seconds=math.ceil(cpu_core_time))
        print('apply_af_filters: All done in: {}'.format(str(ttd)))
        print('apply_af_filters: CPU Cores time: {}'.format(str(ctd)))

        # check that the original files were replaced with their denoised versions
        denoised_hashes = {fname: FSH.file_md5(fname, hex=True) for fname in media_files}
        for hash_key in orig_hashes.keys():
            self.assertNotEqual(orig_hashes[hash_key], denoised_hashes[hash_key])

        # cleanup
        backup_dirs = ffutils.get_backup_dirs(self.src_dir, recursive = recursive)
        fpathes = [fpath for b_d in backup_dirs for fpath in ffutils.get_media_files(src_dir = b_d)]
        # move all backed-up file back to their origin
        for fpath in fpathes:
            fpath_dir, fpath_fname = os.path.split(fpath)
            fpath_parent_dir = os.path.dirname(fpath_dir)
            fpath_to_parent = os.path.join(fpath_parent_dir, fpath_fname)
            shutil.move(fpath, fpath_to_parent)
        # ditch the backup dirs
        for b_d in backup_dirs:
            if os.path.exists(b_d):
                os.rmdir(b_d)

        # check that all got back to the originals
        restored_hashes = {fname: FSH.file_md5(fname, hex=True) for fname in media_files}
        for hash_key in orig_hashes.keys():
            self.assertEqual(orig_hashes[hash_key], restored_hashes[hash_key])



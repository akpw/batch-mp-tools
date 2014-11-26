
#!/usr/bin/env python
# coding=utf8
## Copyright (c) 2014 Arseniy Kuznetsov
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

import unittest, os, inspect, sys
import shutil, hashlib, datetime
from test_ffmp_base import FFMPTest
import batchmp.ffmptools.ffmputils as utils
from batchmp.ffmptools.ffmp import FFMP

class FFMPTests(FFMPTest):
    def setUp(self):
        super(FFMPTests, self).setUp()
        self.ffmp = FFMP(self.src_dir)

    def test_get_media_length(self):
        media_files = utils.get_media_files(self.src_dir, recursive = True)
        for fpath in media_files:
            fname = os.path.split(fpath)[1]
            length = self.ffmp.get_media_length(fpath)
            self.assertTrue(abs(length - self.media_info[fname]) < 2)

    def test_apply_af_filters_raise(self):
        self.assertRaises(utils.FFmpegArgsError, self.ffmp.apply_af_filters)

    def test_apply_af_filters(self):
        print('Now testing applying filters, might take a while...')
        media_files = utils.get_media_files(src_dir = self.src_dir, recursive = True)

        # get the original media files md5 hashes
        orig_hashes = {fname: self.file_md5(fname, hex=True) for fname in media_files}

        hpass, lpass, num_passes, recursive, quiet = 200, 0, 4, True, False
        cpu_core_time, total_elapsed = self.ffmp.apply_af_filters(
                                                highpass=hpass,
                                                lowpass=lpass,
                                                num_passes=num_passes,
                                                recursive = recursive,
                                                quiet=quiet)
        ttd = datetime.timedelta(seconds=total_elapsed)
        ctd = datetime.timedelta(seconds=cpu_core_time)
        print('apply_af_filters: All done in: {}'.format(str(ttd)[:10]))
        print('apply_af_filters: CPU Cores time: {}'.format(str(ctd)[:10]))

        # check that the original files were replaced with their denoised versions
        denoised_hashes = {fname: self.file_md5(fname, hex=True) for fname in media_files}
        for hash_key in orig_hashes.keys():
            self.assertNotEqual(orig_hashes[hash_key], denoised_hashes[hash_key])

        # cleanup
        backup_dirs = utils.get_backup_dirs(self.src_dir, recursive = recursive)
        fpathes = [fpath for b_d in backup_dirs for fpath in utils.get_media_files(src_dir = b_d)]
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
        restored_hashes = {fname: self.file_md5(fname, hex=True) for fname in media_files}
        for hash_key in orig_hashes.keys():
            self.assertEqual(orig_hashes[hash_key], restored_hashes[hash_key])

if __name__ == "__main__":
    if sys.version_info >= (3, 0):
        unittest.main()



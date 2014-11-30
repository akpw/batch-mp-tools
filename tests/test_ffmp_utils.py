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


import unittest, os, inspect, sys
import shutil, hashlib, datetime
from test_ffmp_base import FFMPTest
import batchmp.ffmptools.ffmputils as utils

class FFMPUtilsTests(FFMPTest):
    def setUp(self):
        super(FFMPUtilsTests, self).setUp()
        self.bkp_dirs_ptrn = ['{0}data{0}mp3{0}{1}'.format(os.path.sep, utils.BACKUP_DIR_PREFIX),
                              '{0}data{0}mp4{0}{1}'.format(os.path.sep, utils.BACKUP_DIR_PREFIX)]

    def test_ffmpeg_installed(self):
        self.assertTrue(utils.ffmpeg_installed())

    def test_get_media_files(self):
        media_files = [os.path.split(fpath)[1]
            for fpath in utils.get_media_files(self.src_dir, recursive = True)]
        self.assertTrue(set(media_files) == set(self.media_info.keys()))

    def test_setup_backup_dirs(self):
        media_files = utils.get_media_files(self.src_dir, recursive = True)
        backup_dirs = utils.setup_backup_dirs(media_files)

        # should return a backup dir for every file
        self.assertTrue(len(backup_dirs) == len(media_files))

        # some of the test files are into same backup dirs
        self.assertTrue(len(set(backup_dirs)) < len(media_files))

        for b_d in backup_dirs:
            # test the naming pattern
            found = b_d.find(self.bkp_dirs_ptrn[0]) + \
                                b_d.find(self.bkp_dirs_ptrn[1])
            self.assertTrue(found == 0)

            # cleanup
            if os.path.exists(b_d):
                os.rmdir(b_d)

    def test_get_backup_dirs(self):
        media_files = utils.get_media_files(self.src_dir, recursive = True)
        backup_dirs = utils.setup_backup_dirs(media_files)

        backup_dirs_list = utils.get_backup_dirs(self.src_dir, recursive = True)
        self.assertEqual(set(backup_dirs), set(backup_dirs_list))

        for b_d in backup_dirs_list:
            # cleanup
            if os.path.exists(b_d):
                os.rmdir(b_d)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_run_shell(self):
        cmd = "ls"
        utils.run_cmd(cmd)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_run_shell_raise(self):
        cmd = "which"
        self.assertRaises(utils.CmdProcessingError, utils.run_cmd, cmd)

if __name__ == "__main__":
    if sys.version_info >= (3, 0):
        unittest.main()




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
from batchmp.ffmptools.ffutils import FFH, CmdProcessingError, run_cmd


class FFMPUtilsTests(FFMPTest):

    def test_ffmpeg_installed(self):
        self.assertTrue(FFH.ffmpeg_installed())

    def test_media_files(self):
        media_info = {'00 Background noise.mp3': 6,
                           '01 Background noise.mp4': 116,
                           '02 Background noise.mp4': 175}
        media_files = [os.path.basename(fpath)
            for fpath in FFH.media_files(self.src_dir, exclude = 'bmfp*')]

        self.assertTrue(set(media_files) == set(media_info.keys()))

    def test_setup_backup_dirs(self):
        media_files = [f for f in FFH.media_files(self.src_dir, exclude = 'bmfp*')]
        backup_dirs = FFH.setup_backup_dirs(media_files)

        # should return a backup dir for every file
        self.assertTrue(len(backup_dirs) == len(media_files))

        # some of the test files are into same backup dirs
        self.assertTrue(len(set(backup_dirs)) < len(media_files))

        bkp_dirs_ptrn = ['{0}data{0}denoise_a{0}{1}'.format(os.path.sep, FFH.BACKUP_DIR_PREFIX),
                              '{0}data{0}denoise_v{0}{1}'.format(os.path.sep, FFH.BACKUP_DIR_PREFIX)]
        for b_d in backup_dirs:
            # test the naming pattern
            found = b_d.find(bkp_dirs_ptrn[0]) + b_d.find(bkp_dirs_ptrn[1])
            self.assertTrue(found > 0)

            # cleanup
            if os.path.exists(b_d):
                os.rmdir(b_d)

    def test_backup_dirs(self):
        media_files = FFH.media_files(self.src_dir)
        backup_dirs = FFH.setup_backup_dirs(media_files)

        backup_dirs_list = FFH.backup_dirs(self.src_dir)
        self.assertEqual(set(backup_dirs), set(backup_dirs_list))

        for b_d in backup_dirs_list:
            # cleanup
            if os.path.exists(b_d):
                os.rmdir(b_d)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_run_shell(self):
        cmd = "ls"
        run_cmd(cmd)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_run_shell_raise(self):
        cmd = "which"
        self.assertRaises(CmdProcessingError, run_cmd, cmd)

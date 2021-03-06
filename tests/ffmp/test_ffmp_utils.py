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
from batchmp.fstools.walker import DWalker
from batchmp.ffmptools.ffutils import FFH
from batchmp.commons.utils import (
    run_cmd,
    CmdProcessingError
)
from batchmp.fstools.builders.fsprms import FSEntryParamsExt


class FFMPUtilsTests(FFMPTest):

    def test_ffmpeg_installed(self):
        self.assertTrue(FFH.ffmpeg_installed())

    def test_media_files(self):
        media_info = {'00 Background noise.mp3': 6,
                           '01 Background noise.mp4': 116,
                           '02 Background noise.mp4': 175}
        
        fs_entry_params = FSEntryParamsExt()
        fs_entry_params.src_dir = self.src_dir
        fs_entry_params.exclude = 'bmfp*'
   

        pass_filter = lambda fpath: FFH.ffmpeg_supported_media(fpath)
        media_files = [entry.basename for entry in DWalker.file_entries(fs_entry_params, pass_filter = pass_filter)]

        self.assertTrue(set(media_files) == set(media_info.keys()))

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_run_shell(self):
        cmd = "ls"
        run_cmd(cmd)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_run_shell_raise(self):
        cmd = "which"
        self.assertRaises(CmdProcessingError, run_cmd, cmd)



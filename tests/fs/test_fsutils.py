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


import sys, unittest, re
from batchmp.fstools.fsutils import DWalker, FSH
from batchmp.fstools.dirtools import DHandler
from batchmp.ffmptools import ffmputils
from .test_fs_base import FSTest

class FSTests(FSTest):
    def test_dir_stats(self):
        fcnt, dcnt, total_size = DWalker.dir_stats(src_dir = self.src_dir, include_size = True)

        p = re.compile('(\d+)[^\d]*$')

        fcnt_ref = (ffmputils.run_cmd_shell('find {} -type f | wc -l'.format(self.src_dir)))
        res = p.search(fcnt_ref)
        fcnt_ref = int(res.group(1))
        self.assertTrue(fcnt == fcnt_ref)

        dcnt_ref = ffmputils.run_cmd_shell('find {} -type d | wc -l'.format(self.src_dir))
        res = p.search(dcnt_ref)
        dcnt_ref = int(res.group(1)) - 1 # not counting src_dir
        self.assertTrue(dcnt == dcnt_ref)

    def test_fs_flatten_folders(self):
        DWalker.flatten_folders(src_dir = self.src_dir,
                                target_depth = 0, include='unit*', filter_dirs = False)

        # remove excessive folders
        FSH.remove_empty_folders_below_target_depth(self.src_dir, target_depth = 0)

        self.resetDataFromBackup(quiet=True)

    def test_print_dir(self):
        print('\nTest Data:')
        DHandler.print_dir(src_dir = self.src_dir, max_depth = 4,
                                    include = '*', exclude = 'nested_3',
                                    filter_dirs = True, filter_files = True)



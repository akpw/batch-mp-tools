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

import os, sys, unittest
from batchmp.fstools.fsutils import DWalker, FSH
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.rename import Renamer
from .test_fs_base import FSTest

class FSTests(FSTest):
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_dir_stats(self):
        fcnt, dcnt, total_size = DHandler.dir_stats(src_dir = self.src_dir, include_size = True)

        cmd = 'find {} -type f | wc -l'.format(self.src_dir)
        fcnt_ref = self.get_last_digit_from_shell_cmd(cmd)
        self.assertTrue(fcnt == fcnt_ref)

        cmd = 'find {} -type d | wc -l'.format(self.src_dir)
        dcnt_ref = self.get_last_digit_from_shell_cmd(cmd)  - 1 # not counting the src_dir
        self.assertTrue(dcnt == dcnt_ref)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_fs_flatten_folders(self):
        DHandler.flatten_folders(src_dir = self.src_dir,
                                target_level = 0, include = '*', filter_dirs = False, quiet = True)

        fcnt, dcnt, _ = DHandler.dir_stats(src_dir = self.src_dir)
        self.assertTrue(fcnt == 30 and dcnt == 0)
        self.resetDataFromBackup(quiet=True)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_renamer_replace(self):
        Renamer.replace(src_dir = self.src_dir, end_level = 4,
                                find_str = r'test', replace_str = r'flower',
                                include_dirs = True, quiet = True)

        cmd = 'find {} -type f -iname "*flower*" | wc -l'.format(self.src_dir)
        fcnt = self.get_last_digit_from_shell_cmd(cmd)

        self.assertTrue(fcnt == 22)
        self.resetDataFromBackup(quiet=True)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_renamer_add_index(self):
        Renamer.add_index(src_dir = self.src_dir, end_level = 5,
                                include = '[!.]*', exclude='test_*',
                                as_prefix = True, join_str = ' ',
                                include_dirs = True, min_digits = 2, quiet = True)

        cmd = "find {} | grep '[0-9][0-9] ' | grep -v 'test_' | grep -v '.DS_Store' | wc -l".format(self.src_dir)
        fcnt = self.get_last_digit_from_shell_cmd(cmd)

        self.assertTrue(fcnt == 23)
        self.resetDataFromBackup(quiet=True)


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_remove_n_characters(self):
        Renamer.remove_n_characters(src_dir = self.src_dir, end_level = 2,
                                num_chars = 2, from_head = True,
                                include = '*', exclude = '',
                                filter_dirs = True, filter_files = True,
                                include_dirs = True, include_files = True, quiet = True)

        cmd = "find {} -type f | grep 'st_[0-9]' | wc -l".format(self.src_dir)
        fcnt = self.get_last_digit_from_shell_cmd(cmd)

        self.assertTrue(fcnt == 14)
        self.resetDataFromBackup(quiet=True)


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_add_text(self):
        Renamer.add_text(src_dir = self.src_dir, end_level = 4,
                                text = 'The', as_prefix = True, join_str = ' ',
                                include = '*', exclude = '',
                                filter_dirs = True, filter_files = True,
                                include_dirs = False, include_files = True, quiet = True)

        cmd = "find {} -type f | grep 'The ' | wc -l".format(self.src_dir)
        fcnt = self.get_last_digit_from_shell_cmd(cmd)

        self.assertTrue(fcnt == 30)
        self.resetDataFromBackup(quiet=True)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_add_date(self):
        Renamer.add_date(src_dir = self.src_dir,
                                as_prefix = False, join_str = '_', format = '%Y-%m-%d',
                                end_level = 5, include = '*', exclude = '',
                                filter_dirs = True, filter_files = True,
                                include_dirs = False, include_files = True, quiet = True)

        cmd = 'find {} -type f | grep "_[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]" | wc -l'.format(self.src_dir)
        fcnt = self.get_last_digit_from_shell_cmd(cmd)

        self.assertTrue(fcnt == 30)
        self.resetDataFromBackup(quiet=True)


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_delete_non_media(self):
        Renamer.delete(src_dir = self.src_dir, end_level = 1,
                                include = '*png',
                                filter_dirs = False,
                                include_dirs = False,
                                non_media_files_only = True, quiet = True)

        cmd = 'find {} -maxdepth 2 | wc -l'.format(self.src_dir)
        fcnt = self.get_last_digit_from_shell_cmd(cmd) - 1 # not counting the src_dir

        self.assertTrue(fcnt == 7)
        self.resetDataFromBackup(quiet=True)














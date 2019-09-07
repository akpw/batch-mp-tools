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

import os, sys, unittest, shlex
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.rename import Renamer
from batchmp.fstools.builders.fsentry import FSEntry, FSEntryParamsBase, FSEntryParamsExt, FSEntryParamsFlatten
from .test_fs_base import FSTest


class FSTests(FSTest):
    def setUp(self):
        self.resetDataFromBackup(quiet=True)

    def tearDown(self):
        self.resetDataFromBackup(quiet=True)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_dir_stats(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_dir_stats
        fs_entry_params = self._fs_entry()
        fcnt, dcnt, total_size = DHandler.dir_stats(fs_entry_params, include_size = True)

        cmd = 'find {} -type f | grep -v ".DS_Store" | wc -l'.format(shlex.quote(self.src_dir))
        fcnt_ref = self.get_last_digit_from_shell_cmd(cmd)
        self.assertTrue(fcnt == fcnt_ref, msg = '{0} files, should be {1}'.format(fcnt, fcnt_ref))

        cmd = 'find {} -type d | wc -l'.format(shlex.quote(self.src_dir))
        dcnt_ref = self.get_last_digit_from_shell_cmd(cmd) - 1 #not counting the  root dir
        self.assertTrue(dcnt == dcnt_ref, msg = '{0} dirs, should be {1}'.format(dcnt, dcnt_ref))

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_dir_stats_filtered_folders(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_dir_stats_filtered_folders
        fs_entry_params = self._fs_entry(include = 'nested_a*;nested_c', filter_dirs = True, filter_files = False)
        _, dcnt, _ = DHandler.dir_stats(fs_entry_params, include_size = True)

        cmd = 'find {} -type d -iname "nested_a*" -or -iname "nested_c" | wc -l'.format(shlex.quote(self.src_dir))
        dcnt_ref = self.get_last_digit_from_shell_cmd(cmd)
        self.assertTrue(dcnt == dcnt_ref, msg = '{0} dirs, should be {1}'.format(dcnt, dcnt_ref))


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_fs_flatten_folders(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_fs_flatten_folders
        fs_entry_params = self._fs_entry()
        fcnt_orig, _, _ = DHandler.dir_stats(fs_entry_params)

        fsf_entry_params = self._fs_entry(flatten = True)
        DHandler.flatten_folders(fsf_entry_params, remove_non_empty_folders = True)
        
        fcnt, dcnt, _ = DHandler.dir_stats(fs_entry_params)
        self.assertTrue(fcnt == fcnt_orig, msg = '{0} files, should be {1}'.format(fcnt, fcnt_orig))
        self.assertTrue(dcnt == 0, msg = '{} directories, should be 0'.format(dcnt))

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_renamer_replace(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_renamer_replace
        fs_entry_params = self._fs_entry(end_level = 4, include = '*test*')
        fcnt_orig, _, _ = DHandler.dir_stats(fs_entry_params)

        Renamer.replace(fs_entry_params, find_str = 'test', replace_str = 'flower')

        fs_entry_params.include = '*flower*'
        fcnt, _, _ = DHandler.dir_stats(fs_entry_params)
        self.assertTrue(fcnt == fcnt_orig, msg = '{0} files, should be {1}'.format(fcnt, fcnt_orig))

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_renamer_add_index_sequential(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_renamer_add_index_sequential
        fs_entry_params = self._fs_entry(end_level = 5, include = 'last*')        
        fcnt_orig, _, _ = DHandler.dir_stats(fs_entry_params)

        join_str = ' '
        Renamer.add_index(fs_entry_params, sequential = True, join_str = join_str, as_prefix = True, min_digits = 2)

        fs_entry_params.include = '[0-9][0-9]{}last*'.format(join_str)
        fcnt, _, _ = DHandler.dir_stats(fs_entry_params)
        self.assertTrue(fcnt == fcnt_orig, msg = '{0} files, should be {1}'.format(fcnt, fcnt_orig))

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_renamer_add_index_multilevel(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_renamer_add_index_multilevel
        fs_entry_params = self._fs_entry(end_level = 5, include = '[!.]*', exclude = 'test_*')        
        fcnt_orig, _, _ = DHandler.dir_stats(fs_entry_params)

        join_str = ' '
        Renamer.add_index(fs_entry_params, as_prefix = True, join_str = join_str, min_digits = 2)

        fs_entry_params.include = '[0-9][0-9]{}*'.format(join_str)
        fcnt, _, _ = DHandler.dir_stats(fs_entry_params)
        self.assertTrue(fcnt == fcnt_orig, msg = '{0} files, should be {1}'.format(fcnt, fcnt_orig))


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_remove_n_characters(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_remove_n_characters
        fs_entry_params = self._fs_entry(end_level = 2, include = 'test_[0-9]')        
        fcnt_orig, _, _ = DHandler.dir_stats(fs_entry_params)

        Renamer.remove_n_characters(fs_entry_params, num_chars = 2, from_head = True)

        fs_entry_params.include = 'st_[0-9]'
        fcnt, _, _ = DHandler.dir_stats(fs_entry_params)
        self.assertTrue(fcnt == fcnt_orig, msg = '{0} files, should be {1}'.format(fcnt, fcnt_orig))


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_add_text(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_add_text
        fs_entry_params = self._fs_entry(end_level = 4)        
        fcnt_orig, _, _ = DHandler.dir_stats(fs_entry_params)

        join_str = ' '
        Renamer.add_text(fs_entry_params, text = 'The', as_prefix = True, join_str = join_str)

        fs_entry_params.include = 'The{}*'.format(join_str)
        fcnt, _, _ = DHandler.dir_stats(fs_entry_params)
        self.assertTrue(fcnt == fcnt_orig, msg = '{0} files, should be {1}'.format(fcnt, fcnt_orig))


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_add_date(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_add_date
        fs_entry_params = self._fs_entry(end_level = 5)        
        fcnt_orig, _, _ = DHandler.dir_stats(fs_entry_params)

        join_str = '_'
        Renamer.add_date(fs_entry_params, as_prefix = False, join_str = join_str, format = '%Y-%m-%d')

        fs_entry_params.include = '*{}[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*'.format(join_str)
        fcnt, _, _ = DHandler.dir_stats(fs_entry_params)
        self.assertTrue(fcnt == fcnt_orig, msg = '{0} files, should be {1}'.format(fcnt, fcnt_orig))


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_delete_files(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_delete_files
        fs_entry_params_all_files = self._fs_entry(end_level = 4)
        fcnt_all, _, _ = DHandler.dir_stats(fs_entry_params_all_files)

        fs_entry_params = self._fs_entry(end_level = 4, include = '*week*')        
        fcnt_del, _, _ = DHandler.dir_stats(fs_entry_params)

        Renamer.delete(fs_entry_params)

        fcnt, _, _ = DHandler.dir_stats(fs_entry_params_all_files)
        fcnt_remaining = fcnt_all - fcnt_del
        self.assertTrue(fcnt == fcnt_remaining, msg = '{0} files, should be {1}'.format(fcnt, fcnt_remaining))


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_delete_folders(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_delete_folders
        # renamer -el 5 -in 'nested_c;nested_a*' -fd delete -id -dc
        fs_entry_params_all_files = self._fs_entry(end_level = 5, filter_files = False)
        fcnt_all, dcnt_all, _ = DHandler.dir_stats(fs_entry_params_all_files)

        fs_del_entry_params = self._fs_entry(end_level = 5, 
                                            include = 'nested_c;nested_a*', 
                                            filter_dirs = True, filter_files = False, 
                                            include_dirs = True)        
        fcnt_del, dcnt_del, _ = DHandler.dir_stats(fs_del_entry_params)

        Renamer.delete(fs_del_entry_params)

        fcnt, dcnt, _ = DHandler.dir_stats(fs_entry_params_all_files)

        fcnt_remaining = fcnt_all - fcnt_del
        dcnt_remaining = dcnt_all - dcnt_del
        self.assertTrue(fcnt == fcnt_remaining, msg = '{0} files, should be {1}'.format(fcnt, fcnt_remaining))
        self.assertTrue(dcnt == dcnt_remaining, msg = '{0} dirs, should be {1}'.format(dcnt, dcnt_remaining))


    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_delete_non_media(self):
        ## python -m unittest tests.fs.test_fsutils.FSTests.test_delete_non_media
        # renamer -el 1 -in '*week*' delete -nm
        fs_entry_params_all_files = self._fs_entry(end_level = 1)
        fcnt_all, dcnt_all, _ = DHandler.dir_stats(fs_entry_params_all_files)

        fs_del_entry_params = self._fs_entry(end_level = 1, include = '*week*')        
        fcnt_del, _, _ = DHandler.dir_stats(fs_del_entry_params)

        Renamer.delete(fs_del_entry_params, non_media_files_only = True)

        fcnt, _, _ = DHandler.dir_stats(fs_entry_params_all_files)
        fcnt_remaining = fcnt_all - fcnt_del
        self.assertTrue(fcnt == fcnt_remaining, msg = '{0} files, should be {1}'.format(fcnt, fcnt_remaining))


    def _fs_entry(self, include = FSEntry.DEFAULT_INCLUDE, exclude = FSEntry.DEFAULT_EXCLUDE, 
                        filter_dirs = False, filter_files = True, 
                        include_dirs = False, include_files = True, quiet = True,
                        end_level = sys.maxsize, start_level = 0, flatten = False, target_level = 0, display_current = False, show_size = False):

        args = {
            'dir' : self.src_dir,
            'start_level' : start_level,
            'end_level' : end_level,
            'include' : include,
            'exclude' : exclude,
            'filter_dirs' : filter_dirs,
            'all_files' : not filter_files,
            'include_dirs' : include_dirs,
            'exclude_files' : not include_files,
            'target_level' : target_level,
            'show_size' : show_size,
            'display_current' : display_current,
            'quiet' : quiet
        }
        
        fs_entry_params = FSEntryParamsExt(args) if not flatten else FSEntryParamsFlatten(args)

        return fs_entry_params












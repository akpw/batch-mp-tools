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
import ffmptools.ffmputils as utils
from ffmptools.ffmp import FFMP

class FFMPTest(unittest.TestCase):
    def setUp(self):
        self.src_dir = os.path.join(os.curdir, 'data')
        self.media_info = {'00 Background noise.mp3': 6,
                           '01 Background noise.mp4': 116,
                           '02 Background noise.mp4': 175}

    @classmethod
    def setUpClass(cls):
        ''' If needed, resets tests data to its original state
        '''
        src_dir = os.path.join(os.curdir, 'data')
        bckp_dir = os.path.join(os.curdir, '.data')

        # get test media files from both current && hidden backup dirs
        current_media = utils.get_media_files(src_dir = src_dir, recursive = True)
        bckp_media = utils.get_media_files(src_dir = bckp_dir, recursive = True)

        # check if the number of files in both dirs matches
        restore_needed = len(current_media) != len(bckp_media)
        if restore_needed:
            print('Need restore on num files')
        if not restore_needed:
            # see if any backup dirs are left
            bckp_dirs = utils.get_backup_dirs(src_dir, recursive = True)
            if bckp_dirs != []:
                print('Need restore on backup dirs:\n', set(bckp_dirs))
                restore_needed = True
        if not restore_needed:
            # compare files hashes
            curent_media_hashes = {os.path.split(fpath)[1]: FFMPTest.file_md5(fpath, hex=True)
                                                                    for fpath in current_media}
            bckp_media_hashes = {os.path.split(fpath)[1]: FFMPTest.file_md5(fpath, hex=True)
                                                                    for fpath in bckp_media}
            restore_needed = set(curent_media_hashes.items()) != set (bckp_media_hashes.items())
            if restore_needed:
                print('Need restore on changes in files:')

        if restore_needed:
            # reset everything back to original
            print('\nRestoring media files...\n')
            shutil.rmtree(src_dir)
            shutil.copytree(bckp_dir, src_dir)

    @staticmethod
    def file_md5(fpath, block_size=0, hex=False):
        """ Calculates MD5 hash for a file at fpath
        """
        md5 = hashlib.md5()
        if block_size == 0:
            block_size = 128 * md5.block_size
        with open(fpath,'rb') as f:
            for chunk in iter(lambda: f.read(block_size), b''):
                md5.update(chunk)
        return md5.hexdigest() if hex else md5.digest()

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
    import sys
    if sys.version_info >= (3, 0):
        unittest.main()




"""
test_dir = os.path.realpath(os.path.dirname(inspect.getfile(inspect.currentframe())))
pkg_dir = os.path.join(test_dir, "ffmptools")
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)
"""

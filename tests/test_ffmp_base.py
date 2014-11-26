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
import batchmp.ffmptools.ffmputils as utils

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


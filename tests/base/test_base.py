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
import shutil, hashlib
import batchmp.ffmptools.ffmputils as utils

class BMPTest(unittest.TestCase):
    src_dir = bckp_dir = None

    @classmethod
    def setUpClass(cls):
        ''' If needed, resets tests data to its original state
        '''
        if cls.src_dir == cls.bckp_dir == None:
            # reset check not required
            return

        # get test files from both current && hidden backup dirs
        data_files = [os.path.join(r,f) for r,d,files in os.walk(cls.src_dir) for f in files]
        bckp_files = [os.path.join(r,f) for r,d,files in os.walk(cls.bckp_dir) for f in files]

        # check if file names in both dirs matches
        restore_needed = set(data_files) != set(bckp_files)
        if restore_needed:
            print('Need restore on files names')
        if not restore_needed:
            # check the dirs
            data_dirs = [os.path.join(r,d) for r,dirs,f in os.walk(cls.src_dir) for d in dirs]
            bckp_dirs = [os.path.join(r,d) for r,dirs,f in os.walk(cls.bckp_dir) for d in dirs]

            if set(data_dirs) != set(bckp_dirs):
                print('Need restore on dirs names:\n', set(bckp_dirs))
                restore_needed = True
        if not restore_needed:
           # compare files hashes
            data_files_hashes = {os.path.basename(fpath): FSH.file_md5(fpath, hex=True)
                                                                    for fpath in data_files}
            bckp_files_hashes = {os.path.basename(fpath): FSH.file_md5(fpath, hex=True)
                                                                    for fpath in bckp_files}
            restore_needed = set(data_files_hashes.items()) != set (bckp_files_hashes.items())
            if restore_needed:
                print('Need restore on changes in files:')

        if restore_needed:
            # reset everything back to original
            print('\nRestoring files...\n')
            shutil.rmtree(cls.src_dir)
            shutil.copytree(cls.bckp_dir, cls.src_dir)
        else:
            print('No restore needed')

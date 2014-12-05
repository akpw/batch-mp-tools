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
from batchmp.fstools.fsutils import FSH

class BMPTest(unittest.TestCase):
    src_dir = bckp_dir = None

    @classmethod
    def setUpClass(cls):
        cls.resetDataFromBackup()

    @classmethod
    def resetDataFromBackup(cls, quiet = False):
        ''' If needed, resets tests data to its original state
        '''
        if cls.src_dir == cls.bckp_dir == None:
            # reset check not required
            return

        # helper functions
        rpath = lambda r,f: os.path.join(os.path.realpath(r),f)
        partial_path = lambda f,s: f[len(s):]

        # check the files
        data_files = [rpath(r,f)
                        for r,d,files in os.walk(cls.src_dir) for f in files]
        bckp_files = [rpath(r,f)
                        for r,d,files in os.walk(cls.bckp_dir) for f in files]
        #  num files
        restore_needed = len(data_files) != len(bckp_files)
        if restore_needed:
            if not quiet:
                print('Need restore on num files mismatch')
        else:
            # file names matches
            restore_needed = set((partial_path(f, cls.src_dir) for f in data_files)) != \
                             set((partial_path(f, cls.bckp_dir) for f in bckp_files))
            if restore_needed:
                if not quiet:
                    print('Need restore on files names mismatch')

        if not restore_needed:
            # check the dirs
            data_dirs = [rpath(r,d)
                            for r,dirs,f in os.walk(cls.src_dir) for d in dirs]
            bckp_dirs = [rpath(r,d)
                            for r,dirs,f in os.walk(cls.bckp_dir) for d in dirs]
            # num dirs
            restore_needed = len(data_dirs) != len(bckp_dirs)
            if restore_needed:
                if not quiet:
                    print('Need restore on num dirs mismatch')
            else:
                # dir names matches
                restore_needed =    set((partial_path(d, cls.src_dir) for d in data_dirs)) != \
                                    set((partial_path(d, cls.bckp_dir) for d in bckp_dirs))
                if restore_needed:
                    if not quiet:
                        print('Need restore on dir names mismatch')

        if not restore_needed:
           # compare files hashes
            data_files_hashes = {partial_path(fpath, cls.src_dir): FSH.file_md5(fpath, hex=True)
                                                        for fpath in data_files}
            bckp_files_hashes = {partial_path(fpath, cls.bckp_dir): FSH.file_md5(fpath, hex=True)
                                                        for fpath in bckp_files}
            restore_needed = set(data_files_hashes.items()) != set (bckp_files_hashes.items())
            if restore_needed:
                if not quiet:
                    print('Need restore on changes in files:')

        if restore_needed:
            # reset everything back to original
            if not quiet:
                print('\nRestoring files...\n')
            shutil.rmtree(cls.src_dir)
            shutil.copytree(cls.bckp_dir, cls.src_dir)
        else:
            if not quiet:
                print('No restore needed')


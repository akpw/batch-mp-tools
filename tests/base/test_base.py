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

        # check the files
        data_fpaths = [rpath(r,f)
                        for r,d,files in os.walk(cls.src_dir) for f in files]
        bckp_fpaths = [rpath(r,f)
                        for r,d,files in os.walk(cls.bckp_dir) for f in files]
        #  num files
        restore_needed = len(data_fpaths) != len(bckp_fpaths)
        if restore_needed:
            if not quiet:
                print('Need restore on num files mismatch')
        else:
            # file names matches
            restore_needed = set((os.path.basename(f) for f in data_fpaths)) != \
                             set((os.path.basename(f) for f in bckp_fpaths))
            if restore_needed:
                if not quiet:
                    print('Need restore on files names mismatch')

        if not restore_needed:
            # check the dirs
            data_dpaths = [rpath(r,d)
                            for r,dirs,f in os.walk(cls.src_dir) for d in dirs]
            bckp_dpaths = [rpath(r,d)
                            for r,dirs,f in os.walk(cls.bckp_dir) for d in dirs]
            # num dirs
            restore_needed = len(data_dpaths) != len(bckp_dpaths)
            if restore_needed:
                if not quiet:
                    print('Need restore on num dirs mismatch')
            else:
                # dir names matches
                restore_needed = set((os.path.basename(d) for d in data_dpaths)) != \
                                 set((os.path.basename(d) for d in bckp_dpaths))
                if restore_needed:
                    if not quiet:
                        print('Need restore on dir names mismatch')

        if not restore_needed:
           # compare files hashes
            data_fpaths_hashes = {os.path.basename(fpath): FSH.file_md5(fpath, hex=True)
                                                        for fpath in data_fpaths}
            bckp_files_hashes = {os.path.basename(fpath): FSH.file_md5(fpath, hex=True)
                                                        for fpath in bckp_fpaths}
            restore_needed = set(data_fpaths_hashes.items()) != set(bckp_files_hashes.items())
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


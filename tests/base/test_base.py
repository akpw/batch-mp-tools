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
        ''' If needed, resets tests data to its original state
        '''
        if cls.src_dir == cls.bckp_dir == None:
            # reset check not required
            return

        # for dir entries, build list of dictionaries {realpath: basepath}
        rpath = lambda r,f: os.path.join(os.path.realpath(r),f)
        base_path = lambda f: os.path.basename(f)

        # check the files
        data_files = [rpath(r,f)
                        for r,d,files in os.walk(cls.src_dir) for f in files]
        bckp_files = [rpath(r,f)
                        for r,d,files in os.walk(cls.bckp_dir) for f in files]
        #  num files
        restore_needed = len(data_files) != len(bckp_files)
        if restore_needed:
            print('Need restore on num files mismatch')
        else:
            # file names matches
            restore_needed = set((base_path(f) for f in data_files)) != \
                                set((base_path(f) for f in bckp_files))
            if restore_needed:
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
                print('Need restore on num dirs mismatch')
            else:
                # dir names matches
                restore_needed =    set((base_path(d) for d in data_dirs)) != \
                                    set((base_path(d) for d in bckp_dirs))
                if restore_needed:
                    print('Need restore on dir names mismatch')

        if not restore_needed:
           # compare files hashes
            data_files_hashes = {base_path(fpath): FSH.file_md5(fpath, hex=True)
                                                        for fpath in data_files}
            bckp_files_hashes = {base_path(fpath): FSH.file_md5(fpath, hex=True)
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




        """
                base_path = lambda f: os.path.os.path.dirname(os.path.split(f)[0])


        base_path = lambda r,f: os.path.join(os.path.dirname(r),f)
        pathes = lambda r,f: {rpath(r,f): base_path(r,f)}

        """

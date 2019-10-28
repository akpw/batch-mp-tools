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


import os, sys
from batchmp.fstools.builders.fsentry import FSEntry, FSEntryType
from batchmp.fstools.builders.fsprms import FSEntryParamsBase
from batchmp.fstools.builders.fsb import FSEntryBuilderBase

class DWalker:
    ''' Walks content of a directory, generating
        a sequence of structured FS elements (FSEntry)
    '''
    @staticmethod
    def entries(fs_entry_params):
        ''' generates a sequence of FSEntries elements
        '''
        # let's walk
        for rpath, dnames, fnames in os.walk(fs_entry_params.src_dir):
            # set the current dir
            fs_entry_params.rpath = rpath

            # check levels
            if fs_entry_params.skip_iteration:
                continue

            # set siblings
            fs_entry_params.fnames = fnames
            fs_entry_params.dnames = dnames

            # sync dnames for sorting / filtering
            dnames[:] = fs_entry_params.merged_dnames

            # yield the current folder
            yield from fs_entry_params.fs_entry_builder.build_root_entry(fs_entry_params)

            ## Files processing ##
            yield from fs_entry_params.fs_entry_builder.build_entry(fs_entry_params)

    @staticmethod
    def file_entries(fs_entry_params, pass_filter = None):
        if not pass_filter:
            pass_filter = lambda f: True

        for entry in DWalker.entries(fs_entry_params):

            if entry.type in (FSEntryType.ROOT, FSEntryType.DIR):
                continue

            if not pass_filter(entry.realpath):
                continue
            else:
                yield entry

    @staticmethod
    def dir_entries(fs_entry_params, pass_filter = None):
        if not pass_filter:
            pass_filter = lambda f: True

        for entry in DWalker.entries(fs_entry_params):

            if entry.type in (FSEntryType.ROOT, FSEntryType.FILE):
                continue

            if not pass_filter(entry.realpath):
                continue
            else:
                yield entry


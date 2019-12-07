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
from abc import ABCMeta, abstractmethod
from batchmp.fstools.fsutils import FSH
from batchmp.fstools.builders.fsentry import FSEntry, FSEntryType, FSMediaEntryGroupType


class FSEntryBuilder(metaclass = ABCMeta):
    ''' root entry builder
    '''
    @staticmethod
    def build_root_entry(fs_entry_params):
        # yield the current folder
        if fs_entry_params.current_level == 0:
            # src dir goes in full and without indent
            entry = FSEntry(type = FSEntryType.ROOT,
                                basename = os.path.basename(fs_entry_params.rpath), 
                                realpath = fs_entry_params.rpath,
                                indent = os.path.dirname(fs_entry_params.rpath) + os.path.sep,
                                isEnclosingEntry = True,
                                isEnclosingFilesContainterEntry = True)
        else:
            entry = FSEntry(FSEntryType.DIR,
                                basename = os.path.basename(fs_entry_params.rpath), 
                                realpath = fs_entry_params.rpath,
                                indent = fs_entry_params.current_indent[:-1] + os.path.sep,
                                isEnclosingEntry = fs_entry_params.isEnclosingEntry,
                                isEnclosingFilesContainterEntry = fs_entry_params.isEnclosingFilesContainterEntry,
                                isScopeSwitchingEntry = True)
        # debug
        # print("{}cur level:{}".format(fs_entry_params.current_indent, fs_entry_params.current_level))
        # print("{}end level:{}".format(fs_entry_params.current_indent, fs_entry_params.end_level))              
        yield entry        

    ''' Abstract builder method
    '''
    @staticmethod
    @abstractmethod
    def build_entry(fs_entry_params):
        yield None


class FSEntryBuilderBase(FSEntryBuilder):
    ''' File System Processing
    '''
    @staticmethod
    def build_entry(fs_entry_params):
        ## not much there for enclosing entries 
        if fs_entry_params.isEnclosingEntry and not fs_entry_params.isEnclosingFilesContainterEntry: 
            return

        ## Files processing ##        
        for fname in fs_entry_params.fnames:
            fpath = os.path.join(fs_entry_params.rpath, fname)
            entry = FSEntry(type = FSEntryType.FILE,
                                basename = fname, 
                                realpath = fpath,
                                indent = fs_entry_params.siblings_indent)
            yield entry

        ## Directories processing ##
        for dname in fs_entry_params.dnames.passed:
           dpath = os.path.join(fs_entry_params.rpath, dname)

           # check the current_level from root
           if fs_entry_params.current_level == fs_entry_params.end_level:
               # not going any deeper
               # yield the dir
               entry = FSEntry(type = FSEntryType.DIR,
                                basename = dname, 
                                realpath = dpath, 
                                indent = fs_entry_params.siblings_indent[:-1] + os.path.sep)
               #print('from build_entry!\n')
               yield entry



class FSEntryBuilderFlatten(FSEntryBuilder):
    @staticmethod
    def build_root_entry(fs_entry_params):
        if fs_entry_params.current_level <= fs_entry_params.target_level:
            yield from FSEntryBuilderBase.build_root_entry(fs_entry_params)


    @staticmethod
    def build_entry(fs_entry_params):
        if fs_entry_params.current_level < fs_entry_params.target_level:
            yield from FSEntryBuilderBase.build_entry(fs_entry_params)
        else: 
            if fs_entry_params.current_level > fs_entry_params.target_level:
                return

            flattens = []
            unique_fname = fs_entry_params.unique_fnames()

            ## Files processing ##        
            for fname in fs_entry_params.fnames:
                fpath = os.path.join(fs_entry_params.rpath, fname)
                entry = FSEntry(type = FSEntryType.FILE, 
                                    basename = fname, 
                                    realpath = fpath, 
                                    indent = fs_entry_params.siblings_indent)
                flattens.append(entry)

                # store the name generator init values
                next(unique_fname)
                unique_fname.send(fname)
            
            ## Directories processing ##
            # remove non-matching
            for dname in fs_entry_params.merged_dnames:
                dpath = os.path.join(fs_entry_params.rpath, dname)

                # flattening, yield the underlying files 
                for dr, _, dfnames in os.walk(dpath):
                    dr_path = FSH.full_path(dr)
                    df_path = lambda fname: os.path.join(dr_path, fname)

                    # filter non-matching files
                    if fs_entry_params.filter_files:
                        dfnames = (fname for fname in dfnames if fs_entry_params.passed_filters(fname))

                    # file types
                    if fs_entry_params.file_type != FSMediaEntryGroupType.ANY:
                        dfnames = [fname for fname in dfnames if fs_entry_params.is_of_required_type(df_path(fname))]


                    for fname in dfnames:
                        fpath = df_path(fname)
                        next(unique_fname)
                        fname = unique_fname.send(fname)

                        entry = FSEntry(FSEntryType.FILE, fname, fpath, fs_entry_params.siblings_indent)
                        flattens.append(entry)

            # OK to sort now
            if fs_entry_params.by_size:
                sort_key = lambda entry: os.path.getsize(entry.realpath)
            else:
                # for sorting need to still derive basename from realpath
                # as for flattened it might be different from entry.basename
                sort_key = lambda entry: os.path.basename(entry.realpath).lower()

            for entry in sorted(flattens, key = sort_key, reverse = fs_entry_params.descending):
                yield entry



class FSEntryBuilderOrganize(FSEntryBuilder):
    @staticmethod
    def build_entry(fs_entry_params):                
        pass

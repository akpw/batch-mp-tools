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


import os, sys, fnmatch, collections, pygtrie, heapq
from enum import IntEnum
from abc import ABCMeta, abstractmethod
from batchmp.fstools.fsutils import FSH
from batchmp.commons.descriptors import (
         PropertyDescriptor,
         LazyFunctionPropertyDescriptor,
         LazyClassPropertyDescriptor,
         FunctionPropertyDescriptor,
         BooleanPropertyDescriptor)

# FSEntry Attributes with default values
class FSEntryDefaultValueDescriptor(LazyFunctionPropertyDescriptor):
    pass


class FSEntryFilteredFilesValueDescriptor(PropertyDescriptor):
    ''' Files property descriptor
    '''
    def __set__(self, instance, value):
        if isinstance(instance, FSEntryParamsBase):
            # filtering
            if instance.filter_files:
                fnames = [fname for fname in value if instance.passed_filters(fname)]
            else:
                fnames = [fname for fname in value]
            # sorting
            if instance.by_size:
                sort_key = lambda fname: os.path.getsize(os.path.join(instance.rpath, fname))
            else:
                sort_key = lambda fname: fname.lower()
            fnames.sort(key = sort_key, reverse = instance.descending)
            # set value
            super().__set__(instance, fnames)
        else:
            raise TypeError("Not a FSEntryParamsBase Type: {}".format(instance.__class__))


DNames = collections.namedtuple('DNames', ['passed', 'enclosing'])
class FSEntryFilteredDirsValueDescriptor(PropertyDescriptor):
    ''' Directories property descriptor
    '''
    def __set__(self, instance, value):
        if isinstance(instance, FSEntryParamsBase):
            passed_dnames, enclosing_dnames = [], []
            # filtering
            if instance.filter_dirs:
                for dname in value:
                    if instance.passed_filters(dname):
                        passed_dnames.append(dname)
                    elif instance.scan_for_enclosing_directories:
                        en_dname = os.path.join(instance.rpath, dname)                        
                        if instance._enclosing_dnames.has_node(en_dname):
                            enclosing_dnames.append(dname)
            else:
                passed_dnames = [dname for dname in value]
            # sorting
            if instance.by_size:
               dirs_sort_key = lambda dname: FSH.dir_size(os.path.join(instance.rpath, dname))
            else:
               dirs_sort_key = lambda dname: dname.lower()
            passed_dnames.sort(key = dirs_sort_key, reverse = instance.descending)
            enclosing_dnames.sort(key = dirs_sort_key, reverse = instance.descending)
            super().__set__(instance, DNames(passed_dnames, enclosing_dnames))
        else:
            raise TypeError("Not a FSEntryParamsBase Type: {}".format(instance.__class__))



class FSEntryRPathDescriptor(PropertyDescriptor):
    ''' RPath property descriptor
    '''
    def __set__(self, instance, value):
        if isinstance(instance, FSEntryParamsBase):
            super().__set__(instance, FSH.full_path(value))
        else:
            raise TypeError("Not a FSEntryParamsBase Type: {}".format(instance.__class__))


class FSEntry:
    ''' File System entry representation
    '''
    def __init__(self, type, basename, realpath, indent, isEnclosingEntry = False):
        self.type = type
        self.basename = basename
        self.realpath = realpath
        self.indent = indent
        self.isEnclosingEntry = isEnclosingEntry

class FSEntryType(IntEnum):
    ROOT = 0
    DIR = 1
    FILE = 2
    IMAGE = 3
    AUDIO = 4
    VIDEO = 5

class FSEntryDefaults:    
    DEFAULT_NESTED_INDENT = '  '
    DEFAULT_INCLUDE = '*'
    DEFAULT_EXCLUDE = '.*' #exclude hidden files
    DEFAULT_SORT = 'na'


class FSEntryParamsBase():
    ''' Base Entry attributes
    '''
    src_dir = PropertyDescriptor()

    start_level = PropertyDescriptor()
    end_level = PropertyDescriptor()

    filter_dirs = BooleanPropertyDescriptor()
    filter_files = BooleanPropertyDescriptor()
    show_size = BooleanPropertyDescriptor()

    include = PropertyDescriptor()
    exclude = PropertyDescriptor()
    nested_indent = PropertyDescriptor()
    sort = PropertyDescriptor()

    fs_entry_builder = LazyClassPropertyDescriptor('batchmp.fstools.builders.fsb.FSEntryBuilderBase')

    '''Runtime attrbutes
    '''
    rpath = FSEntryRPathDescriptor()
    fnames = FSEntryFilteredFilesValueDescriptor()
    dnames = FSEntryFilteredDirsValueDescriptor()
    
    def __init__(self, args = {}):
        self.src_dir = args.get('dir')
        self.start_level = args.get('start_level', 0)
        self.end_level = args.get('end_level', sys.maxsize)
        self.nested_indent = args.get('nested_indent', FSEntryDefaults.DEFAULT_NESTED_INDENT)
        self.include = args.get('include', FSEntryDefaults.DEFAULT_INCLUDE)
        self.exclude = args.get('exclude', FSEntryDefaults.DEFAULT_EXCLUDE)
        self.sort = args.get('sort', FSEntryDefaults.DEFAULT_SORT)
        self.filter_dirs = not args.get('all_dirs', False)
        self.filter_files = not args.get('all_files', False)   
        self.show_size = args.get('show_size', False)

        # enclosing directores
        self._enclosing_dnames = pygtrie.StringTrie(separator=os.path.sep)
        self._enclosing_files_containters = set()
        if self.scan_for_enclosing_directories:
            for rpath, dirs, files in os.walk(self.src_dir):
                if FSH.level_from_root(self.src_dir, rpath) < self.end_level:
                    marked_enclosing = False
                    for dir_name in dirs:
                        if self.passed_filters(dir_name):
                            self._enclosing_dnames[rpath] = rpath
                            marked_enclosing = True
                            break # no need to check this root further
                    for file_name in files:
                        if self.passed_filters(file_name):
                            if not marked_enclosing:
                                self._enclosing_dnames[rpath] = rpath
                            self._enclosing_files_containters.add(rpath)
                            break # no need to check this root further
            #print(self._enclosing_dnames)
            #print()
            #print(self._enclosing_files_containters)

    # Current level
    @property
    def current_level(self):
        return FSH.level_from_root(self.src_dir, self.rpath)        

    # Sorting
    @property
    def descending(self):
        return True if self.sort.endswith('d') else False

    @property
    def by_size(self):
        return True if self.sort.startswith('s') else False

    # Filtering
    @property
    def passed_filters(self):        
        def include_match(fsname):
            for include_pattern in self.include.split(';'):
                if fnmatch.fnmatch(fsname, include_pattern):
                    return True
            return False

        def exclude_match(fsname):
            for exclude_pattern in self.exclude.split(';'):
                if fnmatch.fnmatch(fsname, exclude_pattern):
                    return True
            return False

        return lambda fs_name: include_match(fs_name) and (not exclude_match(fs_name))

    @property
    def scan_for_enclosing_directories(self):
        return self.include != FSEntryDefaults.DEFAULT_INCLUDE and self.end_level > 0    

    @property
    def skip_iteration(self):   
        return True if (self.current_level < self.start_level) or (self.current_level > self.end_level) else False

    @property
    def end_iteration(self):
        return True if self.current_level > self.end_level else False

    @property
    def current_indent(self):
        return '{0}{1}'.format(self.nested_indent * (self.current_level), '|-> ' if not self.isEnclosingEntry else '|.. ')

    @property
    def siblings_indent(self):
        return '{0}{1}'.format(self.nested_indent * (self.current_level + 1), '|- ')

    @property
    def merged_dnames(self):
        return list(heapq.merge(self.dnames.passed, self.dnames.enclosing, reverse = self.descending))

    @property
    def isEnclosingEntry(self):
        dir_name = os.path.basename(self.rpath)
        return self._enclosing_dnames.has_node(self.rpath) and not self.passed_filters(dir_name) and not (self.rpath in self._enclosing_files_containters)


    @classmethod
    def writable_fields(cls):
        ''' generates names of all writable tag fields
        '''
        for c in cls.__mro__:
            for field, descr in vars(c).items():
                if isinstance(descr, LazyClassPropertyDescriptor):
                    continue
                if isinstance(descr, BooleanPropertyDescriptor):
                    yield field
                elif isinstance(descr, PropertyDescriptor):
                    yield field

    # Copy attributes from another entry
    def copy_params(self, fs_entry):
        self._enclosing_dnames = fs_entry._enclosing_dnames
        for field in self.writable_fields():
            value = getattr(fs_entry, field)
            if value is not None:
                setattr(self, field, value)

    def __str__(self):
        return ('Entry of type: {}\n'.format(self.__class__.__name__) + \
            '\n '.join('{}: {}'.format(key, value) for key, value in vars(self).items()))  



class FSEntryParamsExt(FSEntryParamsBase):
    display_current = BooleanPropertyDescriptor()
    include_dirs = BooleanPropertyDescriptor()
    include_files = BooleanPropertyDescriptor()
    quiet = BooleanPropertyDescriptor()

    def __init__(self, args = {}):
        super().__init__(args)
        self.display_current = args.get('display_current', False)
        self.include_dirs = args.get('include_dirs', False)
        self.include_files = not args.get('exclude_files', False)
        self.quiet = args.get('quiet', False)       

    
class FSEntryParamsFlatten(FSEntryParamsExt):
    ''' Flatten Entry attributes
    '''
    fs_entry_builder = LazyClassPropertyDescriptor('batchmp.fstools.builders.fsb.FSEntryBuilderFlatten')
    
    target_level = PropertyDescriptor()
    remove_folders = BooleanPropertyDescriptor()
    remove_non_empty_folders = BooleanPropertyDescriptor()
    unique_fnames = FunctionPropertyDescriptor()

    def __init__(self, args = {}):
        super().__init__(args)
        self.remove_folders = False if args.get('discard_flattened') == 'le' else True
        self.remove_non_empty_folders = True if args.get('discard_flattened') == 'da' else False
        self.unique_fnames = args.get('unique_fnames', FSH.unique_fnames)

        self.target_level = args.get('target_level', 0)
        if self.end_level < self.target_level:
            self.end_level = self.target_level        



class FSEntryParamsOrganize(FSEntryParamsExt):
    ''' Organize Entry attributes
    '''
    def __init__(self, args = {}):
        super().__init__(args)  



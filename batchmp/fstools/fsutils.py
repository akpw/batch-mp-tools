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


import os, sys, fnmatch, shutil
import hashlib
from collections import namedtuple


class UniqueDirNamesChecker:
    ''' Unique file names Helper
    '''
    def __init__(self, src_dir, *, unique_fnames = None):
        self._uname_gen = unique_fnames() if unique_fnames else FSH.unique_fnames()

        # init the generator function with file names from given source directory
        fnames = [fname for fname in os.listdir(src_dir)]
                                            #if os.path.isfile(os.path.join(src_dir, fname))]
        for fname in fnames:
            next(self._uname_gen)
            self._uname_gen.send(fname)

    def unique_name(self, fname):
        ''' Returns unique file name
        '''
        next(self._uname_gen)
        return self._uname_gen.send(fname)


class FSH:
    ''' FS helper utilities
    '''
    @staticmethod
    def full_path(path):
        return  os.path.realpath(os.path.expanduser(path))

    @staticmethod
    def is_subdir(subdir_path, parent_path):
        subdir_path = FSH.full_path(subdir_path)
        parent_path = FSH.full_path(parent_path)

        relative = os.path.relpath(subdir_path, start=parent_path)

        return not relative.startswith(os.pardir)

    @staticmethod
    def level_from_root(root_path, nested_path):
        ''' determines the level from root_path folder
        '''
        return FSH.full_path(nested_path).count(os.path.sep) - \
                            FSH.full_path(root_path).count(os.path.sep)

    @staticmethod
    def folders_at_level(src_dir, target_level):
        ''' generates a sequence of folders at given level from src_dir
        '''
        for r,d,f in os.walk(src_dir):
           if FSH.level_from_root(src_dir, r) == target_level:
                yield FSH.full_path(r)

    @staticmethod
    def remove_folders_below_target_level(src_dir, target_level=sys.maxsize, empty_only=True):
        ''' removes folders below target level
        '''
        folders_removed = 0
        for tpath in FSH.folders_at_level(src_dir, target_level):
            for r,d,f in os.walk(tpath, topdown = False):
                for dname in d:
                    dpath = os.path.join(r,dname)
                    if not (empty_only and os.listdir(dpath)):
                        folders_removed +=1
                        shutil.rmtree(dpath)
        return folders_removed

    @staticmethod
    def unique_fnames():
        ''' default unique file names generator method,
            via appending a simple numbering pattern
        '''
        unique_names = {}
        while True:
            fname = yield
            while True:
                if fname in unique_names:
                    unique_names[fname] += 1
                    name_base, name_ext = os.path.splitext(fname)
                    fname = '{0}_{1}{2}'.format(name_base, unique_names[fname], name_ext)
                else:
                    unique_names[fname] = 0
                    yield fname
                    break

    @staticmethod
    def fs_size(size, kb_1024=False):
        ''' human readable file system entry size
        '''
        if size < 0:
            raise ValueError('File size can not be negative')
        unit_sfx = {1000: ['KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
                    1024: ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']}
        div = 1024 if kb_1024 else 1000
        for suffix in unit_sfx[div]:
            size /= div
            if size < div:
                if suffix in ('KB', 'KiB'):
                    return '{0:.0f}{1}'.format(size, suffix)
                else:
                    return '{0:.1f}{1}'.format(size, suffix)
        raise ValueError('File is way too large')

    @staticmethod
    def dir_size(dir_path):
        ''' Calculates directory size in bytes
        '''
        total_size = 0
        seen = set()
        for r, _, fnames in os.walk(dir_path):
            for fname in fnames:
                fpath = os.path.join(r, fname)
                try:
                    stat = os.stat(fpath)
                except OSError:
                    continue

                if stat.st_ino in seen:
                    continue
                else:
                    seen.add(stat.st_ino)

                total_size += stat.st_size
        return total_size

    @staticmethod
    def file_md5(fpath, block_size=0, hex=False):
        ''' Calculates MD5 hash for a file at fpath
        '''
        md5 = hashlib.md5()
        if block_size == 0:
            block_size = 128 * md5.block_size
        with open(fpath,'rb') as f:
            for chunk in iter(lambda: f.read(block_size), b''):
                md5.update(chunk)
        return md5.hexdigest() if hex else md5.digest()

    @staticmethod
    def files(src_dir, *, recursive = False, pass_filter = None):
        ''' list of files passing specified filter
        '''
        if not pass_filter:
            pass_filter = lambda f: True
        if recursive:
            fpathes = [os.path.join(r,f) for r,d,files in os.walk(src_dir)
                                                for f in files if pass_filter(f)]
        else:
            fpathes = (os.path.join(src_dir, fname) for fname in os.listdir(src_dir)
                                                                    if pass_filter(fname))
            fpathes = [f for f in fpathes if os.path.isfile(f)]

        return fpathes

    @staticmethod
    def move_FS_entry(orig_path, target_path,
                      check_unique = True,
                      quiet = False, stop = False):
        succeeded = False
        try:
            if check_unique and os.path.exists(target_path):
                raise OSError('\nTarget path entry already exists')
            shutil.move(orig_path, target_path)
            succeeded = True
        except OSError as e:
            if not quiet:
                print(str(e))
                print('Failed to move entry:\n\t{0}\n\t{1}'.format(orig_path, target_path))
                print('Exiting...') if stop else print('Skipping...')
            if stop:
                sys.exit(1)
        return succeeded

    @staticmethod
    def remove_FS_entry(entry_path, include_read_only = False):
        ''' Remove files / dirs,
            can deal with with read-only files
        '''
        def check_writable(fpath):
            if include_read_only and (not os.access(fpath, os.W_OK)):
                os.chmod(fpath, stat.S_IWUSR)
                return True
            else:
                return False

        def onerror(func, fpath, exc_info):
            if check_writable(fpath):
                func(fpath)
            else:
                raise

        entry_path = FSH.full_path(entry_path)
        if os.path.isfile(entry_path):
            check_writable(entry_path)
            os.remove(entry_path)

        elif os.path.isdir(entry_path):
            shutil.rmtree(entry_path, onerror = onerror)


class DWalker:
    ''' Walks content of a directory, generating
        a sequence of structured FS elements (FSEntry)
    '''
    ENTRY_TYPE_ROOT = 'R'
    ENTRY_TYPE_DIR = 'D'
    ENTRY_TYPE_FILE = 'F'

    DEFAULT_NESTED_INDENT = '  '
    DEFAULT_INCLUDE = '*'
    DEFAULT_EXCLUDE = '.*' #exclude hidden files
    DEFAULT_SORT = 'na'

    FSEntry = namedtuple('FSEntry', ['type', 'basename', 'realpath', 'indent'])

    @staticmethod
    def entries(src_dir, *,
                    start_level = 0, end_level = sys.maxsize,
                    include = None, exclude = None,
                    sort = None, nested_indent = None,
                    filter_dirs = True, filter_files = True,
                    flatten = False, ensure_uniq = False, unique_fnames = FSH.unique_fnames):
        ''' generates a sequence of FSEntries elements
            supports recursion to end_level
            supports slicing directory by folder levels
            supports flattening beyond end_level, with optional checking for unique file names
            include / exclude patterns (Unix style)
            sorting:
                'na' / 'nd': by name / by name descending
                'sa' / 'sd': by size / by size descending
        '''
        # check inputs
        if nested_indent is None:
            nested_indent = DWalker.DEFAULT_NESTED_INDENT
        if include is None:
            include = DWalker.DEFAULT_INCLUDE
        if exclude is None:
            exclude = DWalker.DEFAULT_EXCLUDE
        if sort is None:
            sort = DWalker.DEFAULT_SORT

        src_dir = FSH.full_path(src_dir)

        # sorting
        reversed = True if sort.endswith('d') else False
        by_size = True if sort.startswith('s') else False

        # filtering
        def include_match(fsname):
            for include_pattern in include.split(';'):
                if fnmatch.fnmatch(fsname, include_pattern):
                    return True
            return False

        def exclude_match(fsname):
            for exclude_pattern in exclude.split(';'):
                if fnmatch.fnmatch(fsname, exclude_pattern):
                    return True
            return False

        passed_filters = lambda fs_name: include_match(fs_name) and (not exclude_match(fs_name))

        # let's walk
        for r, dnames, fnames in os.walk(src_dir):
            # check the levels
            current_level = FSH.level_from_root(src_dir, r)
            if current_level < start_level:
                continue
            if current_level > end_level and not flatten:
                return

            # indents
            current_indent  = '{0}{1}'.format(nested_indent * (current_level), '|- ')
            siblings_indent = '{0}{1}'.format(nested_indent * (current_level + 1), '|- ')

            # yield the current folder
            rpath = FSH.full_path(r)
            if current_level == 0:
                # src dir goes in full and without indent
                entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_ROOT,
                                            os.path.basename(rpath), rpath,
                                                os.path.dirname(rpath) + os.path.sep)
            else:
                entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_DIR,
                                            os.path.basename(rpath), rpath,
                                                current_indent[:-1] + os.path.sep)
            yield entry

            ## Files processing ##
            # filter non-matching
            if filter_files:
                fnames = [fname for fname in fnames if passed_filters(fname)]

            # flattening folders?
            flattening = flatten and (current_level == end_level)
            if flattening:
                # need to postpone yielding / check for file name uniqueness
                flattens = []
                if ensure_uniq:
                    unique_fname = unique_fnames()
            else:
                # OK to sort now
                if by_size:
                    sort_key = lambda fname: os.path.getsize(os.path.join(rpath,fname))
                else:
                    sort_key = lambda fname: fname.lower()
                fnames.sort(key = sort_key, reverse = reversed)

            for fname in fnames:
                fpath = os.path.join(rpath, fname)
                entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_FILE, fname, fpath, siblings_indent)
                if not flattening:
                    yield entry
                else:
                    flattens.append(entry)
                    if ensure_uniq:
                        # store the name generator init values
                        next(unique_fname)
                        unique_fname.send(fname)

            ## Directories processing ##
            # remove non-matching
            if filter_dirs:
                dnames[:] = [dname for dname in dnames if passed_filters(dname)]
            # Sort
            if by_size:
                dirs_sort_key = lambda dname: FSH.dir_size(os.path.join(rpath, dname))
            else:
                dirs_sort_key = lambda dname: dname.lower()
            dnames.sort(key = dirs_sort_key, reverse = reversed)

            for dname in dnames[:]:
                dpath = os.path.join(rpath, dname)

                # check the current_level from root
                if current_level == end_level:
                    # not going any deeper
                    if not flattening:
                        # yield the dir
                        entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_DIR,
                                            dname, dpath, siblings_indent[:-1] + os.path.sep)
                        yield entry
                    else:
                        # flattening, yield the underlying files instead
                        for dr, _, dfnames in os.walk(dpath):
                            # filter non-matching files
                            if filter_files:
                                dfnames = (fname for fname in dfnames if passed_filters(fname))
                            for fname in dfnames:
                                fpath = FSH.full_path(os.path.join(dr, fname))
                                if ensure_uniq:
                                    next(unique_fname)
                                    fname = unique_fname.send(fname)
                                entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_FILE,
                                                    fname, fpath, siblings_indent)
                                flattens.append(entry)
                    dnames.remove(dname)

            # if flattening, time to render
            if flattening:
                # OK to sort now
                if by_size:
                    sort_key = lambda entry: os.path.getsize(entry.realpath)
                else:
                    # for sorting need to still derive basename from realpath
                    # as for flattened it might be different from entry.basename
                    sort_key = lambda entry: os.path.basename(entry.realpath).lower()
                for entry in sorted(flattens, key = sort_key, reverse = reversed):
                    yield entry

    @staticmethod
    def file_entries(src_dir, *,
                    sort = None, nested_indent = None,
                    start_level = 0, end_level = sys.maxsize,
                    include = None, exclude = None,
                    filter_dirs = True, filter_files = True,
                    pass_filter = None):

        if not pass_filter:
            pass_filter = lambda f: True

        for entry in DWalker.entries(src_dir,
                                        sort = sort, nested_indent = nested_indent,
                                        start_level = start_level, end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files):

            if entry.type in (DWalker.ENTRY_TYPE_ROOT, DWalker.ENTRY_TYPE_DIR):
                continue

            if not pass_filter(entry.realpath):
                continue
            else:
                yield entry

    @staticmethod
    def dir_entries(src_dir, *,
                    sort = None, nested_indent = None,
                    start_level = 0, end_level = sys.maxsize,
                    include = None, exclude = None,
                    filter_dirs = True, filter_files = True,
                    pass_filter = None):

        if not pass_filter:
            pass_filter = lambda f: True

        for entry in DWalker.entries(src_dir,
                                        sort = sort, nested_indent = nested_indent,
                                        start_level = start_level, end_level = end_level,
                                        include = include, exclude = exclude,
                                        filter_dirs = filter_dirs, filter_files = filter_files):

            if entry.type in (DWalker.ENTRY_TYPE_ROOT, DWalker.ENTRY_TYPE_FILE):
                continue

            if not pass_filter(entry.realpath):
                continue
            else:
                yield entry


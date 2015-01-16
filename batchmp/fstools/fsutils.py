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

import os, sys, fnmatch, shutil, tempfile
import hashlib
from collections import namedtuple
from contextlib import contextmanager

@contextmanager
def temp_dir():
    """ Temp dir context manager
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        yield tmp_dir
    finally:
        # remove tmp dir
        shutil.rmtree(tmp_dir)

class FSH(object):
    """ FS helper
    """
    @staticmethod
    def level_from_root(root, nested_path):
        """ determines the level from root folder
        """
        return os.path.realpath(nested_path).count(os.path.sep) - \
                            os.path.realpath(root).count(os.path.sep)

    @staticmethod
    def folders_at_level(src_dir, target_level):
        """ generates a sequence of folders at given level from src_dir
        """
        root_depth = os.path.realpath(src_dir).count(os.sep)
        for r,d,f in os.walk(src_dir):
           if FSH.level_from_root(src_dir, r) == target_level:
                yield os.path.realpath(r)

    @staticmethod
    def remove_folders_below_target_level(src_dir, target_level=sys.maxsize, empty_only=True):
        """ removes folders below target level
        """
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
        """ generates unique file names
        """
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

    def file_size(size, kb_1024=False):
        """ human readable file size
        """
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

    @staticmethod
    def get_files(src_dir=os.curdir, recursive = False, pass_filter = lambda f: True):
        """ gets all files from source directory and (if recursive) its subdirectories
        """
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

class DWalker(object):
    """ Walks content of a directory, generating
        a sequence of structured directory elements (FSEntry)
    """
    ENTRY_TYPE_ROOT = 'R'
    ENTRY_TYPE_DIR = 'D'
    ENTRY_TYPE_FILE = 'F'

    FSEntry = namedtuple('FSEntry', ['type', 'basename', 'realpath', 'indent'])

    @staticmethod
    def entries(src_dir,
                    start_level = 0, end_level = sys.maxsize,
                    include = '*', exclude = '', sort = 'n',
                    filter_dirs = True, filter_files = True,
                    flatten = False, ensure_uniq = False, unique_fname = FSH.unique_fnames()):
        """ generates a sequence of FSEntries elements
            supports recursion to end_level
            supports slicing directory by folder levels
            supports flattening beyond end_level, with optional checking for unique file names
            allows for include / exclude patterns (Unix style)
            sorting:
                'na' / 'nd': by name / by name descending
                'sa' / 'sd': by size / by size descending
        """

        # sorting
        reversed = True if sort.endswith('d') else False
        by_size = True if sort.startswith('s') else False

        # filtering
        passed_filters = lambda s: fnmatch.fnmatch(s, include) and not fnmatch.fnmatch(s, exclude)

        for r, dnames, fnames in os.walk(src_dir):
            # remove non-matching subfolders
            if filter_dirs:
                for dname in sorted(dnames):
                    if not passed_filters(dname):
                        dnames.remove(dname)

            # check the levels
            current_level = FSH.level_from_root(src_dir, r)
            if current_level < start_level:
                continue
            if current_level > end_level and not flatten:
                return

            # indents
            current_indent  = '{0}{1}'.format("\t" * (current_level), '|- ')
            siblings_indent = '{0}{1}'.format("\t" * (current_level + 1), '|- ')

            # yield current folder
            rpath = os.path.realpath(r)
            basename = os.path.basename(r)
            if current_level == 0:
                # src dir goes in full and without indent
                entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_ROOT,
                                        basename, rpath, os.path.dirname(rpath) + os.path.sep)
            else:
                entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_DIR,
                                        basename, rpath, current_indent[:-1] + os.path.sep)
            yield entry

            # filter non-matching files
            if filter_files:
                fnames = (fname for fname in fnames if passed_filters(fname))

            # files sort key
            if by_size:
                sort_key = lambda fname: os.path.getsize(os.path.join(r,fname))
            else:
                sort_key = lambda fname: fname

            # process files
            # if flattening, need to postpone yielding
            # and check for file name uniqueness, if required
            if flatten:
                flattens = []

            for fname in sorted(fnames, key = sort_key, reverse = reversed):
                fpath = os.path.realpath(os.path.join(r, fname))
                entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_FILE, fname, fpath, siblings_indent)
                if not flatten:
                    yield entry
                else:
                    flattens.append(entry)
                    if ensure_uniq:
                        # store the name generator init values
                        next(unique_fname)
                        unique_fname.send(fname)

            # dirs
            for dname in sorted(dnames):
                dpath = os.path.realpath(os.path.join(r, dname))

                # check the current_level from root
                if current_level == end_level:
                    # not going any deeper
                    if not flatten:
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
                                fpath = os.path.realpath(os.path.join(dr, fname))
                                if ensure_uniq:
                                    next(unique_fname)
                                    fname = unique_fname.send(fname)
                                entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_FILE,
                                                    fname, fpath, siblings_indent)
                                flattens.append(entry)
                    dnames.remove(dname)

            # if flattening, time to render
            if flatten:
                if by_size:
                    sort_key = lambda entry: os.path.getsize(entry.realpath)
                else:
                    sort_key = lambda entry: os.path.basename(entry.realpath)
                for entry in sorted(flattens, key = sort_key, reverse = reversed):
                    yield entry

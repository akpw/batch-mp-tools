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
from distutils.util import strtobool

class FSH(object):
    """ FS helper
    """
    @staticmethod
    def level_from_root(root, nested_path):
        return os.path.realpath(nested_path).count(os.path.sep) - \
                            os.path.realpath(root).count(os.path.sep)

    @staticmethod
    def folders_at_level(src_dir, target_level):
        """ generates a sequence of folders at given level from src_dir
        """
        root_depth = os.path.realpath(src_dir).count(os.sep)
        for r,d,f in os.walk(src_dir):
           if FSH.level_from_root(src, r) == target_level:
                yield rpath

    @staticmethod
    def remove_empty_folders_below_target_level(src_dir, target_level):
        """ removes empty folders below target level
        """
        for tpath in FSH.folders_at_level(src_dir, target_level):
            for r,d,f in os.walk(tpath, topdown = False):
                for dname in d:
                    dpath = os.path.join(r,dname)
                    if not os.listdir(dpath):
                        os.rmdir(dpath)

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
        """Gets all files from source directory and (if recursive) its subdirectories
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
    def get_user_input(quiet = False):
        answer = input('\nProceed? [y/n]: ')
        try:
            answer = True if strtobool(answer) else False
        except ValueError:
            print('Not confirmative, exiting')
            return False

        if not quiet:
            if answer:
                print('Confirmed, processing...')
            else:
                print('Not confirmed, exiting')

        return answer

class DWalker(object):
    """ Walks content of a directory
    """
    ENTRY_TYPE_ROOT = 'R'
    ENTRY_TYPE_DIR = 'D'
    ENTRY_TYPE_FILE = 'F'

    FSEntry = namedtuple('FSEntry', ['type', 'basename', 'realpath', 'indent'])

    @staticmethod
    def entries(src_dir, start_level = 0, end_level = sys.maxsize,
                                    include = '*', exclude = '', sort = 'n',
                                    filter_dirs = True, filter_files = True,
                                    flatten = False, ensure_uniq = False):
        """ generates a sequence of directory elements
            supports recursion, include / exclude patterns, sorting
            supports start level and end_level (slicing directory by folder levels)
            supports flattening, with optional checking for unique file names
        """

        # sorting
        reversed = True if sort.endswith('d') else False
        by_size = True if sort.startswith('s') else False

        # filtering
        passed_filters = lambda s: fnmatch.fnmatch(s, include) and not fnmatch.fnmatch(s, exclude)

        for r, dnames, fnames in os.walk(src_dir):
            # current level from the src_dir root
            current_level = FSH.level_from_root(src_dir, r)
            if current_level < start_level:
                continue

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
                                        basename, rpath, current_indent)
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
                if ensure_uniq:
                    unique_name = FSH.unique_fnames()

            for fname in sorted(fnames, key = sort_key, reverse = reversed):
                fpath = os.path.realpath(os.path.join(r, fname))
                entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_FILE, fname, fpath, siblings_indent)
                if not flatten:
                    yield entry
                else:
                    flattens.append(entry)
                    if ensure_uniq:
                        # store the name generator init values
                        next(unique_name)
                        unique_name.send(fname)

            # dirs
            for dname in sorted(dnames):
                dpath = os.path.realpath(os.path.join(r, dname))

                # remove non-matching subfolders
                if filter_dirs:
                    if not passed_filters(dname):
                        dnames.remove(dname)
                        continue

                # check the current_level from root
                if current_level == end_level:
                    # not going any deeper
                    if not flatten:
                        # yield the dir
                        entry = DWalker.FSEntry(DWalker.ENTRY_TYPE_DIR,
                                            dname, dpath, siblings_indent)
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
                                    next(unique_name)
                                    fname = unique_name.send(fname)
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

    @staticmethod
    def flatten_folders(src_dir, target_level = sys.maxsize,
                            include = '*', exclude = '',
                            filter_dirs = True, filter_files = True, quiet = False):
        """ moves files from folders below target current_level
            to their respective parent folders at target level
            checks for file names uniqueness
        """
        for entry in DWalker.entries(src_dir = src_dir,
                                    start_level = target_level, end_level=target_level,
                                    include = include, exclude = exclude,
                                    filter_dirs = filter_dirs, filter_files = filter_files,
                                    flatten = True, ensure_uniq = True):

            flattened_dirs_cnt = flattened_files_cnt = 0
            if entry.type in (DWalker.ENTRY_TYPE_DIR, DWalker.ENTRY_TYPE_ROOT):
                if FSH.level_from_root(src_dir, entry.realpath) == target_level:
                    target_dir_path = entry.realpath
                else:
                    flattened_dirs_cnt += 1
            else:
                if FSH.level_from_root(src_dir, entry.realpath) > target_level:
                    target_fpath = os.path.join(target_dir_path, entry.basename)
                    shutil.move(entry.realpath, target_fpath)
                    flattened_files_cnt += 1

        # print summary
        if not quiet:
            print('Flattened: {0} files, {1} folders'.format(flattened_files_cnt, flattened_dirs_cnt))


# Quick dev testing
if __name__ == '__main__':
   for entry in DWalker.entries(src_dir = '/Users/AKPower/_Dev/GitHub/batch-mp-tools',
                                    end_level = 2,
                                    include = '*', exclude = '',
                                    filter_dirs = True, filter_files = True):
        pass

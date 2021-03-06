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
    def full_path(path, check_parent_path = False):
        if path:
            path = os.path.expanduser(path)
            path = os.path.expandvars(path)
            path = os.path.abspath(path)
            path = os.path.realpath(path)

        # for files, check that the parent dir exists
        if check_parent_path:
            if not os.access(os.path.dirname(path), os.W_OK):
                print('Non-valid path:\n\t "{}"'.format(path))
                sys.exit(1)

        return path if path else None

    @staticmethod
    def path_components(path):
        path = FSH.full_path(path)
        return path.split(os.path.sep) if path else None        

    @staticmethod
    def path_extension(path):
        components = FSH.path_components(path)
        return os.path.splitext(components[-1])[1][1:] if components else None    

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
    def remove_folders_below_target_level(src_dir, target_level=sys.maxsize, empty_only=True, non_empty_msg = None):
        ''' removes folders below target level
        '''
        folders_removed = 0
        for tpath in FSH.folders_at_level(src_dir, target_level):
            for crpath, dnames, _ in os.walk(tpath, topdown = False):
                for dname in dnames:
                    dpath = os.path.join(crpath, dname)
                    if not (empty_only and os.listdir(dpath)):
                        folders_removed +=1
                        shutil.rmtree(dpath)
                    else:
                        print('not empty: {}'.format(dpath))
                        if non_empty_msg:
                            print(non_empty_msg)
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
    def dir_size(dir_path, shared_cache = None):
        ''' Calculates directory size in bytes
        '''
        total_size = 0
        use_shared_cache = isinstance(shared_cache, dict)

        for r, _, fnames in os.walk(dir_path):   
            # for repetitive calls, look to get from provided shared cache
            if use_shared_cache:
                r_size_from_cache = shared_cache.get(r)
                if r_size_from_cache:
                    total_size += r_size_from_cache
                    continue

            # caculate current root size
            r_size = 0            
            r_size += os.path.getsize(r)
            for fname in fnames:
                fpath = os.path.join(r, fname)
                try:
                    stat = os.stat(fpath)
                except OSError:
                    continue
                r_size += stat.st_size

            total_size += r_size
            if use_shared_cache:
                shared_cache[r] = r_size

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

    @staticmethod
    def fs_entry(fpath):
        pass


# Quick dev test
if __name__ == '__main__':
    from batchmp.commons.utils import timed
    path = os.path.realpath(os.path.dirname(__file__))

    @timed
    def dir_size_test(n):    
        for i in range(n):
            size = FSH.dir_size(path, shared_cache)
        return size

    repeat_cnt = 5000
    shared_cache = {}
    print(dir_size_test(repeat_cnt))    

    shared_cache = None
    print(dir_size_test(repeat_cnt))    


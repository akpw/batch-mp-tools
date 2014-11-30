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


import os, sys, shutil
from collections import deque
import mutagen
import fnmatch
from distutils.util import strtobool

# generates a sequence of folders at given depth from root
def _folders_at_depth(root, target_depth):
    root_depth = os.path.realpath(root).count(os.sep)
    for r,d,f in os.walk(root):
        rpath = os.path.realpath(r)
        if os.path.realpath(rpath).count(os.sep) - root_depth == target_depth:
            yield rpath

TYPE='type'         # 'D' or 'F'
RPATH='rpath'       # full path
INDENTED='indented' # indented reoresentation for printing

def _print_dir_iter(src_dir, max_depth = sys.maxsize, flatten = False,
                                    include = '*', exclude = '', sort = 'n'):
    """ generates typed sequence of directory elemensts
        supports recursion, flattening, include / exclude patterns, sorting
    """
    # sorting
    reversed = True if sort.endswith('d') else False
    by_size = True if sort.startswith('s') else False

    # yield root
    yield {TYPE: 'D',
           RPATH: os.path.realpath(src_dir),
           INDENTED: os.path.realpath(src_dir)}

    # if flattening, postpone yielding (sorting)
    if flatten:
        flattens = []
    root_depth = os.path.realpath(src_dir).count(os.path.sep)
    for r, dnames, fnames in os.walk(src_dir):
        # current folder depth
        depth = os.path.realpath(r).count(os.path.sep)
        # indents
        current_indent  = '{0}{1}'.format("\t" * (depth - root_depth), '|- ')
        siblings_indent = '{0}{1}'.format("\t" * (depth - root_depth + 1), '|- ')

        # yield current folder
        if r != src_dir:
            rname = os.path.basename(os.path.realpath(r))
            yield  {TYPE: 'D', RPATH: os.path.realpath(r),
                            INDENTED: '{0}{1}'.format(current_indent, rname)}

        # filter non-matching files
        fnames_filtered = (fname for fname in fnames
                                    if fnmatch.fnmatch(fname, include)
                                        and not fnmatch.fnmatch(fname, exclude))
        # files sort key
        if by_size:
            sort_key = lambda fname: os.path.getsize(os.path.join(r,fname))
        else:
            sort_key = lambda fname: fname

         # process files
        for fname in sorted(fnames_filtered, key = sort_key, reverse = reversed):
            fpath = os.path.realpath(os.path.join(r, fname))
            entry = {TYPE: 'F', RPATH: fpath,
                        INDENTED: '{0}{1}'.format(siblings_indent, fname)}
            if not flatten:
                yield entry
            else:
                flattens.append(entry)

        # dirs
        for dir in sorted(dnames):
            dpath = os.path.realpath(os.path.join(r, dir))
            dname = os.path.basename(dpath)

            # remove non-matching subfolders
            if not fnmatch.fnmatch(dname, include) or fnmatch.fnmatch(dname, exclude):
                dnames.remove(dir)
                continue

            # check the depth from root
            elif depth - root_depth == max_depth:
                # not going any deeper
                if not flatten:
                    # yield the dir
                    yield  {TYPE: 'D', RPATH: dpath,
                                INDENTED: '{0}{1} '.format(siblings_indent, dname)}
                else:
                    # yield the underlying files instead
                    for dr, _, df in os.walk(dpath):
                        for fname in df:
                            dfpath = os.path.realpath(os.path.join(dr, fname))
                            entry = {TYPE: 'F', RPATH: dfpath,
                                        INDENTED: '{0}{1} '.format(siblings_indent, fname)}
                            flattens.append(entry)
                dnames.remove(dir)

        # if flattening, time to render
        if flatten:
            if by_size:
                sort_key = lambda entry: os.path.getsize(entry[RPATH])
            else:
                sort_key = lambda entry: os.path.basename(entry[RPATH])
            for entry in sorted(flattens, key = sort_key, reverse = reversed):
                yield entry
            flattens = []

def print_dir(src_dir, max_depth = sys.maxsize, flatten = False,
                                    include = '*', exclude = '', sort = 'n'):
    """ Prints content of given directory
        supports recursion to max_depth level
        supports flattening folders beyond max_depth (making their files show at max_depth levels)
        allows for include / exclude patterns (Unix style)
        sorting:
            's' / 'sd': by size / by size descending
            'n' / 'nd': by name / by name descending
    """
    if not os.path.exists(src_dir):
        raise ValueError('Not a valid path')

    for entry in _print_dir_iter(src_dir, max_depth, flatten, include, exclude, sort):
        print(entry[INDENTED])

def flatten_folders(src_dir, target_depth = 2, dry_run = True):
    root_depth = os.path.realpath(src_dir).count(os.sep)
    print('Current source directory structure:')

    print_dir(src_dir, flatten = False)

    print ('\nTargeted new structure:')

    # need to check for uniq file names in a dir
    for entry in _print_dir_iter(src_dir, max_depth=target_depth, flatten=True):
        print(entry[INDENTED])

    answer = input('\nProceed? [y/n]: ')
    try:
        answer = True if strtobool(answer) else False
    except ValueError:
        print('Not confirmative, going to quit')
        sys.exit(1)

    if not answer:
        print('Not confirmed, exiting')
    else:
        # OK to go
        # move files to targe folders
        for tpath in _folders_at_depth(src_dir, target_depth):
            for r,d,f in os.walk(tpath):
                rpath = os.path.realpath(r)
                # move files
                if rpath != tpath:
                    for fname in f:
                        orig_path = os.path.join(rpath, fname)
                        target_path = os.path.join(tpath, fname)
                        shutil.move(orig_path, target_path)
        # remove excessive folders
        for tpath in _folders_at_depth(src_dir, target_depth):
            for r,d,f in os.walk(tpath, topdown = False):
                for dname in d:
                    os.rmdir(os.path.join(r,dname))

    print('\nDone')

# renames all album folders in root dir based on given formatter function
def cleanup_albums_names(src_dir, formatter, dry_run=True):
    def __check_tname(tname):
        """ a simple way to check target names' uniquness,
            via preserving a rotating queue of last 10 names
        """
        prev_fnames = deque(maxlen=10)
        while True:
            if tname in prev_fnames:
                tname = ''.join((tname, '_'))
            yield tname
            prev_fnames.append(tname)

    print('Checking album names...')
    for orig_name in os.listdir(src_dir):
        target_name = formatter(orig_name)
        if not target_name:
            continue
        target_name = next(__check_tname(target_name))
        if target_name != orig_name:
            target_path = os.path.join(src_dir, target_name)
            orig_path = os.path.join(src_dir, orig_name)
            if dry_run:
                print("will change:\n\t{0}\n\t{1}\n".format(orig_path,target_path))
            else:
                shutil.move(orig_path, target_path)
    print('Done\n')

# removes all non-media files from down the root
def remove_non_media_files(src_dir, dry_run=True):
    print('Checking for non-media files...')
    for r,d,f in os.walk(src_dir):
        for fname in f:
            if not fname.endswith(self.__media_files):
                src_file = os.path.join(r, fname)
                if dry_run:
                    print("needs removing: {}".format(src_file))
                else:
                    os.remove(src_file)
    print('Done\n')

# renames all media files down the root (based on their folders names)
def cleanup_media_file_names(src_dir, title_formatter = None, dry_run=True):
    print('Checking media file names...')
    for r,d,f in os.walk(src_dir):
        title = os.path.realpath(r).split('/')[-1]
        if title_formatter:
            title = title_formatter(title)

        media_fnames = [fname for fname in sorted(f) if fname.endswith(self.__media_files)]
        cnt, max_f = 0, len(media_fnames)
        for fname in media_fnames:
            if not fname.endswith(self.__media_files):
                continue
            cnt += 1
            ext = os.path.splitext(fname)[1][1:].strip().lower()
            tname = ''.join(('{0:02} '.format(cnt), title, ' ({0}:{1}).'.format(cnt, max_f), ext))
            target_path = os.path.join(r, tname)
            orig_path = os.path.join(r, fname)
            if target_path == orig_path:
                continue
            if dry_run:
                print("needs changing:\n\t{0}\n\t{1}\n".format(orig_path,target_path))
            else:
                shutil.move(orig_path, target_path)
    print('Done\n')


def split_excess_sized_media(src_dir, dry_run = True, chunk_size = 0):
    print('Checking for media with excessive sizes (larger than {}MB)...'.format(FST.GOOGLE_MUSIC_UPLOAD_LIMIT))

    if chunk_size <= 0 or chunk_size >= FST.GOOGLE_MUSIC_UPLOAD_LIMIT:
        chunk_size = FST.GOOGLE_MUSIC_UPLOAD_LIMIT - 10

    # generates excess-seized media
    def __excess_sized_mp3s():
        for r,d,f in os.walk(src_dir):
            for fname in f:
                if fname.endswith('.mp3'):
                    fpath = os.path.join(r, fname)
                    fsize = os.path.getsize(fpath) / 1024**2
                    if fsize  >= FST.GOOGLE_MUSIC_UPLOAD_LIMIT:
                        yield fpath, fsize

    for fpath, fsize in __excess_sized_mp3s():
        print('The file with size {1:.0f}MB excedes the {2}MB limit:\n {0}'
                                .format(fpath, fsize, FST.GOOGLE_MUSIC_UPLOAD_LIMIT))
        if dry_run:
            continue
        if fsize % chunk_size == 0:
            num_parts = fsize / chunk_size
        else:
            num_parts = int(fsize / chunk_size) + 1

        #media = mutagen.File(fpath)
        time_chunk = math.floor(media.info.length/num_parts/60)

        print(' Now splitting into parts of {0}MB / {1} mins...\n'.format(chunk_size, time_chunk))
        path_splitted = os.path.join(os.path.dirname(fpath), '_splitted')
        os.system('mp3splt -q -f -t {0}.0 -a -d "{1}" "{2}"'
                                        .format(time_chunk, path_splitted, fpath))
    print('Done\n')


if __name__ == '__main__':
    root = '/Users/AKPower/Desktop/current/zTest'
    #root = '/Volumes/Misc/Media/_TV/Gotham'
    #root = '/Users/AKPower/Desktop/xTmp'
    #print_dir(root, max_depth = 4, sort = 's', flatten = True, exclude = '.*')

    flatten_folders(root, target_depth=1)

    """
    # set desired folder depth
    mc.flatten_folders(max_depth = 2, dry_run = False)

    # shape up album folders names
    album_pattern = lambda s: re.sub('.*?(?=\d\d).*?|\s-', '', s)
    mc.cleanup_albums_names(album_pattern)

    # remove all non-media files
    mc.remove_non_media_files()

    # shape up individual media file names
    title_formatter = lambda s: re.sub('(\d\d\s)', '', s)
    mc.cleanup_media_file_names(title_formatter)

    # check for excess-sized media
    mc.split_excess_sized_media(dry_run = False, chunk_size = 50)
    """


    """
    def walker(path):
        for r,d,f in os.walk(path):
            print('{0:>10} {1}'.format('Root path:', os.path.realpath(r)))
            for dir in d:
                print('{0:>10} {1}'.format('Dir path:', os.path.realpath(dir)))
            for file in f:
                print('{0:>10} {1}'.format('File path:', os.path.realpath(file)))


     mc.cleanup_albums_names(lambda s: re.sub('.*(?<=\()|\)', '', s), dry_run=False)

                    os.system('ffmpeg -i "{0}" -af "highpass=f=200, lowpass=f=3000" "{1}" -loglevel "error"'
                                                        .format(fpath_input, fpath_output))


    """

    """
    # walker selector (recursive / non recursive)
    def _walker_selector():
        if recursive:
            return os.walk(src_dir)
        else:
            dirs = [dname for dname in os.listdir(src_dir)
                            if os.path.isdir(os.path.join(src_dir, dname))]
            fnames = [fname for fname in os.listdir(src_dir)
                            if os.path.isfile(os.path.join(src_dir, fname))]
            return [(src_dir, dirs, fnames)]
    """

"""
def print_dir(src_dir, max_depth = sys.maxsize, flatten = False,
                                    include = '*', exclude = '', sort = 'n'):
     Prints content of given directory
        supports recursion to max_depth level
        supports flattening folders beyond max_depth (making their files show at max_depth levels)
        allows for include / exclude patterns (Unix style)
        sorting:
            's' / 'sd': by size / by size descending
            'n' / 'nd': by name / by name descending


    if not os.path.exists(src_dir):
        raise ValueError('Not a valid path')

    # sorting selector
    def _sort_selector(r, fnames, sel):
        reversed = True if sel.endswith('d') else False
        if sel.startswith('s'):
            # by size
            sort_sel = sorted(fnames,
                         key = lambda fname: os.path.getsize(os.path.join(r,fname)),
                         reverse=reversed)
        else:
            # by name
            sort_sel = sorted(fnames, reverse=reversed)
        return sort_sel

    # print root
    print(os.path.realpath(src_dir))

    root_depth = os.path.realpath(src_dir).count(os.path.sep)
    for r, dnames, fnames in os.walk(src_dir):
        # current folder depth / indents
        depth = os.path.realpath(r).count(os.path.sep)
        current_indent  = '{0}{1}'.format("\t" * (depth - root_depth), '|- ')
        siblings_indent = '{0}{1}'.format("\t" * (depth - root_depth + 1), '|- ')

        # print current folder
        if r != src_dir:
            rname = os.path.basename(os.path.realpath(r))
            print('{0}{1}'.format(current_indent, rname))

        # print matching files
        for fname in _sort_selector(r, fnames, sort):
            if fnmatch.fnmatch(fname, include) and not fnmatch.fnmatch(fname, exclude):
                print('{0}{1}'.format(siblings_indent, fname))

        # dirs
        for dir in sorted(dnames):
            dpath = os.path.realpath(os.path.join(r, dir))
            dname = os.path.basename(dpath)

            # remove non-matching subfolders
            if not fnmatch.fnmatch(dname, include) or fnmatch.fnmatch(dname, exclude):
                dnames.remove(dir)
                continue

            # check the depth from root
            elif depth - root_depth == max_depth:
                # not going any deeper
                if not flatten:
                    # print the dir
                    print('{0}{1}'.format(siblings_indent, dname))
                else:
                    # print the underlying files instead
                    for _, _, df in os.walk(dpath):
                        for fname in df:
                            print('{0}{1}'.format(siblings_indent, fname))
                dnames.remove(dir)
"""

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


import os, re, datetime, string
from collections import namedtuple
from string import Template
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.builders.fsentry import FSEntry, FSEntryParamsBase
from batchmp.commons.utils import MiscHelpers
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.tags.output.formatters import TagOutputFormatter

class DirsIndexInfo:
    ''' A helper class,
        multi-level indexing indexing info
        for nested directories
    '''
    DirStats = namedtuple('DirStats',
             ['total_files', 'total_dirs', 'files_cnt', 'dirs_cnt'])

    def __init__(self, start_from = 0,
                        include = None, exclude = None,
                        file_pass_filter = None, dir_pass_filter = None):
        self.dirs_info = {}
        self.start_from = start_from
        self.include = include
        self.exclude = exclude
        self.file_pass_filter = file_pass_filter
        self.dir_pass_filter = dir_pass_filter

    def fetch_dir_stats(self, dirname):
        ''' Fetches stats for a directory
        '''
        args = {        
            'dir' : dirname,
            'include' : self.include,
            'exclude' : self.exclude,
            'quiet' : True
        }
        fs_entry_params = FSEntryParamsBase(args) 
        if not dirname in self.dirs_info.keys():
            total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params,
                                                            file_pass_filter = self.file_pass_filter,
                                                            dir_pass_filter = self.dir_pass_filter)
            dir_info = self.DirStats(total_files, total_dirs, self.start_from, self.start_from)
            self.dirs_info[dirname] = dir_info
        return self.dirs_info[dirname]

    def update_dir_stats(self, dirname, dir_stats):
        if dirname in self.dirs_info.keys():
            self.dirs_info[dirname] = dir_stats

    def reset_counters(self):
        for key in self.dirs_info.keys():
            dir_info = self.fetch_dir_stats(key)
            self.dirs_info[key] = self.DirStats(dir_info.total_files, dir_info.total_dirs,
                                                                    self.start_from, self.start_from)
class Renamer(object):
    ''' Renames FS entries
    '''
    @classmethod
    def add_index(cls, fs_entry_params, 
                        as_prefix = False, join_str = '_',
                        start_from = 1, min_digits = 1,
                        sequential = False, by_directory = False):
        ''' adds indexing
            automatically figures out right number of min_digits
        '''
        try:
            start_from = abs(int(start_from))
        except ValueError:
            start_from = 1

        # min digits helper
        def num_digits(num):
            num_digits = MiscHelpers.int_num_digits(num)
            return max(num_digits, min_digits)

        join_str = str(join_str)
        if (sequential or by_directory):
            # for sequential indexing, just use counters
            dirs_cnt = files_cnt = start_from
            total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params)
            def index_sequential(entry):
                nonlocal dirs_cnt, files_cnt
                addition = None
                if entry.type == FSEntry.ENTRY_TYPE_DIR:
                    addition = str(dirs_cnt).zfill(num_digits(total_dirs))

                    # update the dirs counter
                    dirs_cnt += 1

                elif entry.type == FSEntry.ENTRY_TYPE_FILE:
                    if by_directory:
                        # indexing via adding respective directory counter
                        fcnt = dirs_cnt - 1
                        # do nothing for root files
                        if fcnt >= 0:
                            addition = str(fcnt).zfill(num_digits(total_files))
                    else:
                        addition = str(files_cnt).zfill(num_digits(total_files))

                        # need to update the files counter
                        files_cnt += 1

                return addition
        else:
            # for multilevel indexing, need the DirsIndexInfo helper
            dir_info = DirsIndexInfo(start_from = start_from, include = fs_entry_params.include, exclude = fs_entry_params.exclude)
            def index_multilevel(entry):
                addition = None
                parent_dir = os.path.dirname(entry.realpath)
                dir_stats = dir_info.fetch_dir_stats(parent_dir)

                if entry.type == FSEntry.ENTRY_TYPE_DIR:
                    addition = str(dir_stats.dirs_cnt).zfill(num_digits(dir_stats.total_dirs))

                    # need to update the dirs counter
                    dir_stats = dir_info.DirStats(dir_stats.total_files, dir_stats.total_dirs,
                                                        dir_stats.files_cnt, dir_stats.dirs_cnt + 1)
                    dir_info.update_dir_stats(parent_dir, dir_stats)

                elif entry.type == FSEntry.ENTRY_TYPE_FILE:
                    addition = str(dir_stats.files_cnt).zfill(num_digits(dir_stats.total_files))

                    # need to update the files counter
                    dir_stats = dir_info.DirStats(dir_stats.total_files, dir_stats.total_dirs,
                                                        dir_stats.files_cnt + 1, dir_stats.dirs_cnt)
                    dir_info.update_dir_stats(parent_dir, dir_stats)

                return addition

        # set the index function
        index_function = index_sequential if (sequential or by_directory) else index_multilevel
        def add_index_transform(entry):
            addition = None
            # src dir
            if entry.type == FSEntry.ENTRY_TYPE_ROOT:
                pass
            # dirs
            elif entry.type == FSEntry.ENTRY_TYPE_DIR:
                if not fs_entry_params.include_dirs:
                    if by_directory:
                        # here still need to update dirs counter
                        index_function(entry)
                    return entry.basename
                else:
                    addition = index_function(entry)
            # files
            elif entry.type == FSEntry.ENTRY_TYPE_FILE:
                if not fs_entry_params.include_files:
                    return entry.basename
                else:
                    addition = index_function(entry)

            if addition is None:
                return entry.basename
            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        # visualise changes and proceed if confirmed
        proceed = True if fs_entry_params.quiet else DHandler.visualise_changes(fs_entry_params, formatter = add_index_transform)
        if proceed:
            # reset counters
            if (sequential or by_directory):
                dirs_cnt = files_cnt = start_from
            else:
                dir_info.reset_counters()

            # ...and rename
            DHandler.rename_entries(fs_entry_params, formatter = add_index_transform)

    @classmethod
    def capitalize(cls, fs_entry_params):
        ''' capitalizes names of FS entries
        '''

        def capitalize_transform(entry):
            if entry.type == FSEntry.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_FILE and not fs_entry_params.include_files:
                return entry.basename
            return string.capwords(entry.basename)

        # visualise changes and proceed if confirmed
        proceed = True if fs_entry_params.quiet else DHandler.visualise_changes(fs_entry_params, formatter = capitalize_transform)
        if proceed:
            DHandler.rename_entries(fs_entry_params, formatter = capitalize_transform, check_unique = False)


    @classmethod
    def add_date(cls, fs_entry_params, as_prefix = False, join_str = '_', format = '%Y-%m-%d'):
        ''' adds current date
        '''
        addition = datetime.datetime.now().strftime(format)
        join_str = str(join_str)

        def add_date_transform(entry):
            if entry.type == FSEntry.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_FILE and not fs_entry_params.include_files:
                return entry.basename

            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        # visualise changes and proceed if confirmed
        proceed = True if fs_entry_params.quiet else DHandler.visualise_changes(fs_entry_params, formatter = add_date_transform)
        if proceed:
            DHandler.rename_entries(fs_entry_params, formatter = add_date_transform)

    @classmethod
    def add_text(cls, fs_entry_params, text, as_prefix = False, join_str = ' '):
        ''' adds text
        '''
        addition = text
        join_str = str(join_str)

        def add_text_transform(entry):
            if entry.type == FSEntry.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_FILE and not fs_entry_params.include_files:
                return entry.basename

            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        # visualise changes and proceed if confirmed
        proceed = True if fs_entry_params.quiet else DHandler.visualise_changes(fs_entry_params, formatter = add_text_transform)
        if proceed:
            DHandler.rename_entries(fs_entry_params, formatter = add_text_transform)

    @classmethod
    def remove_n_characters(cls, fs_entry_params, num_chars = 0, from_head = True):
        ''' removes n first characters
        '''
        num_chars = abs(num_chars)

        def remove_n_chars_transform(entry):
            if entry.type == FSEntry.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_FILE and not fs_entry_params.include_files:
                return entry.basename

            name_base, name_ext = os.path.splitext(entry.basename)
            if from_head:
                name_base = name_base[num_chars:]
            else:
                name_base = name_base[:-num_chars]
            return ''.join((name_base, name_ext))

        # visualise changes and proceed if confirmed
        proceed = True if fs_entry_params.quiet else DHandler.visualise_changes(fs_entry_params, formatter = remove_n_chars_transform)
        if proceed:
            DHandler.rename_entries(fs_entry_params, formatter = remove_n_chars_transform)

    @classmethod
    def replace(cls, fs_entry_params, find_str, replace_str, case_insensitive=False, include_extension = False):
        ''' Regexp-base replace
        '''
        flags = re.UNICODE
        if case_insensitive:
            flags = flags | re.IGNORECASE
        p = re.compile(find_str, flags)

        def replace_transform(entry):
            if entry.type == FSEntry.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_FILE and not fs_entry_params.include_files:
                return entry.basename

            name_base, name_ext = os.path.splitext(entry.basename)
            match = p.search(entry.basename if include_extension else name_base)
            if match:
                if replace_str is not None:
                    # expand templates
                    replace_str_expanded = cls._expand_templates(entry, replace_str)
                    res = p.sub(replace_str_expanded, entry.basename if include_extension else name_base)
                else:
                    res = match.group()
                return '{0}{1}'.format(res, '' if include_extension else name_ext)
            else:
                return entry.basename

        # visualise changes and proceed if confirmed
        proceed = True if fs_entry_params.quiet else DHandler.visualise_changes(fs_entry_params, formatter = replace_transform)
        if proceed:
            DHandler.rename_entries(fs_entry_params, formatter = replace_transform)

    @classmethod
    def delete(cls, fs_entry_params, non_media_files_only = False):

        ''' Deletes selected files
            Support detection of non-media files
        '''        
        if non_media_files_only:
            handler = MutagenTagHandler() + FFmpegTagHandler()

        def delete_transform(entry):
            if entry.type == FSEntry.ENTRY_TYPE_ROOT:
                return entry.basename
            if entry.type == FSEntry.ENTRY_TYPE_DIR and not fs_entry_params.include_dirs:
                return None
            if entry.type == FSEntry.ENTRY_TYPE_FILE and not fs_entry_params.include_files:
                return None

            if non_media_files_only:
                if handler.can_handle(entry.realpath):
                    return None

            # these are to be gone soon...
            return entry.basename

        proceed = True if fs_entry_params.quiet else DHandler.visualise_changes(fs_entry_params, 
                                    formatter = delete_transform, 
                                    after_msg = 'The following files / folders will be deleted')

        if proceed:
            DHandler.remove_entries(fs_entry_params, formatter = delete_transform)

    @classmethod
    def _expand_templates(cls, entry, value):
        ''' expands template values
        '''
        template = Template(value)
        return template.safe_substitute(cls._substitute_dictionary(entry))

    @classmethod
    def _substitute_dictionary(cls, entry):
        ''' internal template value substitution
        '''
        sd = {}
        full_dir_name = os.path.dirname(entry.realpath)
        sd['dirname'] = os.path.basename(full_dir_name)
        sd['pardirname'] = os.path.basename(os.path.dirname(full_dir_name))

        sd['adtime'] = datetime.datetime.fromtimestamp(os.path.getatime(entry.realpath))
        sd['cdtime'] = datetime.datetime.fromtimestamp(os.path.getctime(entry.realpath))
        sd['mdtime'] = datetime.datetime.fromtimestamp(os.path.getmtime(entry.realpath))

        sd['atime'] = datetime.datetime.fromtimestamp(os.path.getatime(entry.realpath)).time()
        sd['ctime'] = datetime.datetime.fromtimestamp(os.path.getctime(entry.realpath)).time()
        sd['mtime'] = datetime.datetime.fromtimestamp(os.path.getmtime(entry.realpath)).time()

        sd['adate'] = datetime.datetime.fromtimestamp(os.path.getatime(entry.realpath)).date()
        sd['cdate'] = datetime.datetime.fromtimestamp(os.path.getctime(entry.realpath)).date()
        sd['mdate'] = datetime.datetime.fromtimestamp(os.path.getmtime(entry.realpath)).date()

        # for media files, update with the base tags values
        sd.update(cls._get_tags(entry))        

        return sd

    @classmethod
    def _get_tags(cls, entry):
        ''' media tags values for template value substitution
        '''
        tags = {}
        handler = MutagenTagHandler() + FFmpegTagHandler()
        if handler.can_handle(entry.realpath):
            for field in TagOutputFormatter.COMPACT_FIELDS:
                tags[field] = getattr(handler.tag_holder, field, '')
        return tags


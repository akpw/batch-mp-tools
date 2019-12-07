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
from batchmp.fstools.fsutils import FSH
from batchmp.fstools.builders.fsentry import FSEntry, FSEntryType, FSEntryDefaults
from batchmp.fstools.builders.fsprms import FSEntryParamsBase
from batchmp.commons.utils import MiscHelpers
from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.mtghandler import MutagenTagHandler
from batchmp.tags.output.formatters import TagOutputFormatter


# DirEntry Counters helper
class DirCounters:
    def __init__(self, dirs_cnt = 0, files_cnt = 0, num_files = 0, num_dirs = 0):
        self.dirs_cnt = dirs_cnt
        self.files_cnt = files_cnt
        self.num_files = num_files
        self.num_dirs = num_dirs

    @staticmethod
    def num_digits(number, min_digits):
        return max(MiscHelpers.int_num_digits(number), min_digits)

class Renamer:
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

        counters = {fs_entry_params.src_dir : DirCounters(start_from, start_from, 0, 0)}
        total_files = total_dirs = 0      

        if (sequential or by_directory):                
            total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params)
            cnt_key = fs_entry_params.src_dir # one key to rule them all here

            def index_sequential(entry):
                nonlocal counters
                addition = None

                if entry.type == FSEntryType.DIR:        
                    if fs_entry_params.include_dirs:
                        addition = str(counters[cnt_key].dirs_cnt).zfill(DirCounters.num_digits(total_dirs, min_digits))
                    # update the dirs counter
                    if fs_entry_params.include_dirs or by_directory:
                        counters[cnt_key].dirs_cnt += 1

                elif entry.type == FSEntryType.FILE:
                    if by_directory:
                        # indexing via adding respective directory counter
                        fcnt = counters[cnt_key].dirs_cnt - 1
                        # do nothing for root files
                        if fcnt >= 0:
                            addition = str(fcnt).zfill(Counters.num_digits(total_files, min_digits))
                    else:
                        addition = str(counters[cnt_key].files_cnt).zfill(DirCounters.num_digits(total_files, min_digits))
                        # need to update the files counter
                        counters[cnt_key].files_cnt += 1

                return addition
        else:
            # multilevel indexing
            def index_multilevel(entry):
                nonlocal counters, total_files, total_dirs
                addition = None

                if entry.scopeSwitchingEntry:
                    counters[entry.realpath] = DirCounters(start_from, start_from, 
                                                    len(fs_entry_params.fnames), len(fs_entry_params.dnames.passed))

                cnt = counters[os.path.dirname(entry.realpath)]
                if entry.type == FSEntryType.DIR and fs_entry_params.include_dirs:
                    addition = str(cnt.dirs_cnt).zfill(DirCounters.num_digits(cnt.num_dirs, min_digits))
                    cnt.dirs_cnt += 1
                    total_dirs += 1

                elif entry.type == FSEntryType.FILE:
                    addition = str(cnt.files_cnt).zfill(DirCounters.num_digits(cnt.num_files, min_digits))
                    cnt.files_cnt += 1
                    total_files += 1

                return addition

        # set the index function
        index_function = index_sequential if (sequential or by_directory) else index_multilevel
        def add_index_transform(entry):
            addition = None

            # src dir
            if entry.type == FSEntryType.ROOT:
                pass
            # dirs
            elif entry.type == FSEntryType.DIR:
                addition = index_function(entry)
            # files
            elif entry.type == FSEntryType.FILE:
                if fs_entry_params.include_files:
                    addition = index_function(entry)

            if addition is None:
                return entry.basename
            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        # visualise changes and proceed if confirmed
        if fs_entry_params.quiet:
            proceed = True
        else: 
            proceed, _, _ = DHandler.visualise_changes(fs_entry_params, formatter = add_index_transform)
        
        if proceed:
            counters = {fs_entry_params.src_dir : DirCounters(start_from, start_from, 0, 0)}
            if (total_dirs + total_files) == 0:
                total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params)
            DHandler.rename_entries(fs_entry_params, total_files + total_dirs, formatter = add_index_transform)

    @classmethod
    def capitalize(cls, fs_entry_params):
        ''' capitalizes names of FS entries
        '''

        def capitalize_transform(entry):
            if entry.type == FSEntryType.ROOT:
                return entry.basename
            if entry.type == FSEntryType.DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntryType.FILE and not fs_entry_params.include_files:
                return entry.basename
            return string.capwords(entry.basename)

        # visualise changes and proceed if confirmed
        if fs_entry_params.quiet:
            proceed = True
            total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params)
        else: 
            proceed, total_files, total_dirs = DHandler.visualise_changes(fs_entry_params, formatter = capitalize_transform)

        if proceed:
            DHandler.rename_entries(fs_entry_params, total_files + total_dirs, formatter = capitalize_transform, check_unique = False)


    @classmethod
    def add_date(cls, fs_entry_params, as_prefix = False, join_str = '_', format = '%Y-%m-%d'):
        ''' adds current date
        '''
        addition = datetime.datetime.now().strftime(format)
        join_str = str(join_str)

        def add_date_transform(entry):
            if entry.type == FSEntryType.ROOT:
                return entry.basename
            if entry.type == FSEntryType.DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntryType.FILE and not fs_entry_params.include_files:
                return entry.basename

            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        # visualise changes and proceed if confirmed
        if fs_entry_params.quiet:
            proceed = True
            total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params)
        else: 
            proceed, total_files, total_dirs = DHandler.visualise_changes(fs_entry_params, formatter = add_date_transform)

        if proceed:
            DHandler.rename_entries(fs_entry_params, total_files + total_dirs, formatter = add_date_transform)

    @classmethod
    def add_text(cls, fs_entry_params, text, as_prefix = False, join_str = ' '):
        ''' adds text
        '''
        addition = text
        join_str = str(join_str)

        def add_text_transform(entry):
            if entry.type == FSEntryType.ROOT:
                return entry.basename
            if entry.type == FSEntryType.DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntryType.FILE and not fs_entry_params.include_files:
                return entry.basename

            if as_prefix:
                return join_str.join((addition, entry.basename))
            else:
                name_base, name_ext = os.path.splitext(entry.basename)
                return '{0}{1}{2}{3}'.format(name_base, join_str, addition, name_ext)

        if fs_entry_params.quiet:
            proceed = True
            total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params)
        else: 
            proceed, total_files, total_dirs = DHandler.visualise_changes(fs_entry_params, formatter = add_text_transform)

        if proceed:
            DHandler.rename_entries(fs_entry_params, total_files + total_dirs, formatter = add_text_transform)

    @classmethod
    def remove_n_characters(cls, fs_entry_params, num_chars = 0, from_head = True):
        ''' removes n first characters
        '''
        num_chars = abs(num_chars)

        def remove_n_chars_transform(entry):
            if entry.type == FSEntryType.ROOT:
                return entry.basename
            if entry.type == FSEntryType.DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntryType.FILE and not fs_entry_params.include_files:
                return entry.basename

            name_base, name_ext = os.path.splitext(entry.basename)
            if from_head:
                name_base = name_base[num_chars:]
            else:
                name_base = name_base[:-num_chars]
            return ''.join((name_base, name_ext))

        # visualise changes and proceed if confirmed
        if fs_entry_params.quiet:
            proceed = True
            total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params)
        else: 
            proceed, total_files, total_dirs = DHandler.visualise_changes(fs_entry_params, formatter = remove_n_chars_transform)

        if proceed:
            DHandler.rename_entries(fs_entry_params, total_files + total_dirs, formatter = remove_n_chars_transform)

    @classmethod
    def replace(cls, fs_entry_params, find_str, replace_str, case_insensitive=False, include_extension = False):
        ''' Regexp-base replace
        '''
        flags = re.UNICODE
        if case_insensitive:
            flags = flags | re.IGNORECASE
        p = re.compile(find_str, flags)

        def replace_transform(entry):
            if entry.type == FSEntryType.ROOT:
                return entry.basename
            if entry.type == FSEntryType.DIR and not fs_entry_params.include_dirs:
                return entry.basename
            if entry.type == FSEntryType.FILE and not fs_entry_params.include_files:
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
        if fs_entry_params.quiet:
            proceed = True
            total_files, total_dirs, _ = DHandler.dir_stats(fs_entry_params)
        else: 
            proceed, total_files, total_dirs = DHandler.visualise_changes(fs_entry_params, formatter = replace_transform)

        if proceed:
            DHandler.rename_entries(fs_entry_params, total_files + total_dirs, formatter = replace_transform)

    @classmethod
    def delete(cls, fs_entry_params):

        ''' Deletes selected files
            Support detection of non-media files
        '''        

        if fs_entry_params.filter_dirs & fs_entry_params.include_dirs:
            fs_entry_params.filter_files = False
            fs_entry_params.include_files = True


        def delete_transform(entry):
            if entry.type == FSEntryType.ROOT:
                return entry.basename
            if entry.type == FSEntryType.DIR and not fs_entry_params.include_dirs:
                return None
            if entry.type == FSEntryType.FILE and not fs_entry_params.include_files:
                return None

            # these are to be gone soon...
            return entry.basename

        if fs_entry_params.quiet:
            proceed = True
        else: 
            proceed, _, _ = DHandler.visualise_changes(fs_entry_params, 
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


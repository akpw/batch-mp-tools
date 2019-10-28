#!/usr/bin/env python
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

from batchmp.cli.base.bmp_dispatch import BatchMPDispatcher
from batchmp.cli.tagger.tagger_options import TaggerArgParser, TaggerCommands
from batchmp.commons.utils import ImageLoader
from batchmp.tags.processors.basetp import BaseTagProcessor
from batchmp.tags.handlers.tagsholder import TagHolder
from batchmp.tags.output.formatters import OutputFormatType
from batchmp.fstools.builders.fsprms import FSEntryParamsExt

class TagsDispatcher(BatchMPDispatcher):
    ''' Tagger CLI Commands Dispatcher
    '''
    def __init__(self):
        self.option_parser = TaggerArgParser()

    # Dispatcher
    def dispatch(self):
        ''' Dispatches Tagger commands
        '''
        if not super().dispatch():
            args = self.option_parser.parse_options()
            if args['sub_cmd'] == TaggerCommands.PRINT:
                self.print_dir(args)

            elif args['sub_cmd'] == TaggerCommands.SET:
                self.set_tags(args)

            elif args['sub_cmd'] == TaggerCommands.COPY:
                self.copy_tags(args)

            elif args['sub_cmd'] == TaggerCommands.INDEX:
                self.index(args)

            elif args['sub_cmd'] == TaggerCommands.REMOVE:
                self.remove_tags(args)

            elif args['sub_cmd'] == TaggerCommands.REPLACE:
                self.replace_tags(args)

            elif args['sub_cmd'] == TaggerCommands.CAPITALIZE:
                self.capitalize_tags(args)

            elif args['sub_cmd'] == TaggerCommands.DETAUCH:
                self.detauch_art(args)

            else:
                print('Nothing to dispatch')
                return False

        return True

    # Dispatched Methods
    def print_dir(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        BaseTagProcessor().print_dir(fs_entry_params, 
                show_stats = args['show_stats'],
                format = OutputFormatType.FULL if args['full_format'] else OutputFormatType.COMPACT)

    def set_tags(self, args):
        tag_holder = TagHolder(process_templates = False)
        tag_holder.title = args['title']
        tag_holder.album = args['album']
        tag_holder.artist = args['artist']
        tag_holder.albumartist = args['albumartist']
        tag_holder.genre = args['genre']
        tag_holder.composer = args['composer']
        tag_holder.track = args['track']
        tag_holder.tracktotal = args['tracktotal']
        tag_holder.disc = args['disc']
        tag_holder.disctotal = args['disctotal']
        tag_holder.year = args['year']
        tag_holder.encoder = args['encoder']
        tag_holder.bpm = args['bpm']
        tag_holder.comp = args['compilaton']
        tag_holder.grouping = args['grouping']
        tag_holder.comments = args['comments']
        tag_holder.lyrics = args['lyrics']

        art, art_path_or_url = None, args['artwork']
        if art_path_or_url:
            art = ImageLoader.load_image(art_path_or_url)
        if art:
            tag_holder.art = art

        fs_entry_params = FSEntryParamsExt(args)
        BaseTagProcessor().set_tags_visual(fs_entry_params,
                tag_holder = tag_holder,
                diff_tags_only = args['diff_tags_only'])

    def copy_tags(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        BaseTagProcessor().copy_tags(fs_entry_params,
                tag_holder_path = args['tagholder'],
                diff_tags_only = args['diff_tags_only'])

    def index(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        BaseTagProcessor().index(fs_entry_params,
                diff_tags_only = args['diff_tags_only'], 
                start_from = args['start_from'])

    def remove_tags(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        BaseTagProcessor().remove_tags(fs_entry_params,
                tag_fields = args['tag_fields'],
                diff_tags_only = args['diff_tags_only'])

    def replace_tags(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        BaseTagProcessor().replace_tags(fs_entry_params,
                tag_fields = args['tag_fields'], ignore_case = args['ignore_case'],
                find_str = args['find_str'], replace_str = args['replace_str'],
                diff_tags_only = args['diff_tags_only'])

    def capitalize_tags(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        BaseTagProcessor().capitalize_tags(fs_entry_params,
                tag_fields = args['tag_fields'],
                diff_tags_only = args['diff_tags_only'])

    def detauch_art(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        BaseTagProcessor().detauch_art(fs_entry_params,
                target_dir = args['target_dir'])

def main():
    ''' Tagger entry point
    '''
    TagsDispatcher().dispatch()


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

from batchmp.fstools.builders.fsentry import FSEntryParamsExt
from batchmp.commons.descriptors import (
         PropertyDescriptor,
         BooleanPropertyDescriptor)


class FFEntryParams(FSEntryParamsExt):
    pass


class FFEntryParamsExt(FFEntryParams):
    target_dir = PropertyDescriptor()
    target_dir_prefix = PropertyDescriptor()
    log_level = PropertyDescriptor()
    serial_exec = BooleanPropertyDescriptor()
    preserve_metadata = BooleanPropertyDescriptor()

    target_format = PropertyDescriptor() 
    ff_general_options = PropertyDescriptor()
    ff_other_options = PropertyDescriptor()

    def __init__(self, args = {}):
        super().__init__(args)
        self.target_dir = args.get('target_dir')
        self.log_level = args.get('log_level')
        self.serial_exec = args.get('serial_exec', False)

        self.target_format = args.get('target_format') 
        self.ff_general_options = args.get('ff_general_options', 0)
        self.ff_other_options = args.get('ffmpeg_options')
        self.preserve_metadata = args.get('preserve_metadata', True)
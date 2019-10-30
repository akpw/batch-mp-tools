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

from batchmp.fstools.builders.fsprms import FSEntryParamsExt
from batchmp.ffmptools.ffutils import FFHDefaults
from batchmp.ffmptools.ffrunner import LogLevel
from batchmp.ffmptools.ffcommands.cmdopt import FFmpegCommands
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
        self.log_level = args.get('log_level', LogLevel.QUIET)
        self.serial_exec = args.get('serial_exec', False)

        self.target_format = args.get('target_format') 
        self.ff_general_options = args.get('ff_general_options', 0)
        self.ff_other_options = args.get('ffmpeg_options', FFmpegCommands.CONVERT_COPY_VBR_QUALITY)
        self.preserve_metadata = args.get('preserve_metadata', True)



class FFEntryParamsSilenceSplit(FFEntryParamsExt):
    reset_timestamps = BooleanPropertyDescriptor()
    silence_auto_duration = BooleanPropertyDescriptor()
    
    silence_min_duration = PropertyDescriptor() 
    silence_noise_tolerance_amplitude_ratio = PropertyDescriptor() 
    silence_target_trimmed_duration  = PropertyDescriptor() 


    def __init__(self, args = {}):
        super().__init__(args)
        self.reset_timestamps = args.get('reset_timestamps', False)
        self.silence_auto_duration = args.get('auto_duration', False)

        self.silence_noise_tolerance_amplitude_ratio = args.get('noise_tolerance', FFHDefaults.DEFAULT_SILENCE_NOISE_TOLERANCE)
        
        min_duration = args.get('min_duration')
        self.silence_min_duration = min_duration.total_seconds() if min_duration else FFHDefaults.DEFAULT_SILENCE_MIN_DURATION

        trimmed_duration = args.get('trimmed_duration')
        self.silence_target_trimmed_duration = trimmed_duration.total_seconds() if trimmed_duration else FFHDefaults.DEFAULT_SILENCE_TARGET_TRIMMED_DURATION










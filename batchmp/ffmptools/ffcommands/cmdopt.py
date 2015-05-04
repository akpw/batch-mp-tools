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


from enum import Enum, IntEnum


class FFmpegCommands:
    ''' Common FFmpeg commands / options
    '''
    MAP_ALL_STREAMS = ' -map 0'
    COPY_CODECS = ' -c copy'

    # excluding streams
    DISABLE_VIDEO = ' -vn'
    DISABLE_AUDIO = ' -an'
    DISABLE_SUBTITLES = ' -sn'

    # Conversion options
    CONVERT_COPY_VBR_QUALITY = ' -q:v 0 -q:a 0'
    CONVERT_LOSSLESS = ' CONVERT_LOSSLESS_IF_POSSIBLE'
    CONVERT_LOSSLESS_ALAC = ' -q:v 0 -acodec alac'
    CONVERT_LOSSLESS_FLAC = ' -q:v 0 -acodec flac'
    CONVERT_CHANGE_CONTAINER = ' -c copy -copyts'

    # Log level
    LOG_LEVEL_ERROR = ' -v error'
    LOG_LEVEL_QUIET = ' -v quiet'

    # Segment
    SEGMENT = ' -f segment'
    SEGMENT_TIME = ' -segment_time'
    SEGMENT_TIMES = ' -segment_times'
    SEGMENT_RESET_TIMESTAMPS = ' -reset_timestamps 1'

    @staticmethod
    def exclude_input_stream(stream_idx):
        return ' -map -0:{}'.format(stream_idx)

    @staticmethod
    def include_input_stream(stream_idx):
        return ' -map 0:{}'.format(stream_idx)


class FFmpegBitMaskOptions(IntEnum):
    ''' FFmpeg commands / options bitmasks
    '''
    MAP_ALL_STREAMS = (1<<0)
    COPY_CODECS = (1<<1)

    DISABLE_VIDEO = (1<<5)
    DISABLE_AUDIO = (1<<6)
    DISABLE_SUBTITLES = (1<<7)

    @classmethod
    def ff_general_options(cls, ff_gbm_options):
        options_str = ''
        if ff_gbm_options:
            for bm_option in cls:
                if bm_option & ff_gbm_options == bm_option:
                    options_str = ''.join((options_str, cls._option_str_value(bm_option)))
        return options_str

    @staticmethod
    def _option_str_value(bm_option):
        if bm_option == FFmpegBitMaskOptions.MAP_ALL_STREAMS:
            return FFmpegCommands.MAP_ALL_STREAMS
        elif bm_option == FFmpegBitMaskOptions.COPY_CODECS:
            return FFmpegCommands.COPY_CODECS

        elif bm_option == FFmpegBitMaskOptions.DISABLE_VIDEO:
            return FFmpegCommands.DISABLE_VIDEO
        elif bm_option == FFmpegBitMaskOptions.DISABLE_AUDIO:
            return FFmpegCommands.DISABLE_AUDIO
        elif bm_option == FFmpegBitMaskOptions.DISABLE_SUBTITLES:
            return FFmpegCommands.DISABLE_SUBTITLES

        else:
            return ''

# Quick dev test
if __name__ == '__main__':
    copy_codecs = True
    options = 0
    options |= FFmpegBitMaskOptions.DISABLE_SUBTITLES
    if copy_codecs:
        options |= FFmpegBitMaskOptions.COPY_CODECS
    options |= FFmpegBitMaskOptions.DISABLE_VIDEO
    print(FFmpegBitMaskOptions.ff_general_options(options))

    exclude_stream = 1
    print('exclude video stream {}: {}'.format(exclude_stream, FFmpegCommands.exclude_input_stream(exclude_stream)))






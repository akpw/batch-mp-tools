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


import os, subprocess, shlex, sys
import time, datetime, json, re
from collections import namedtuple
from batchmp.fstools.builders.fsentry import FSMediaEntryType
from batchmp.commons.utils import (
    run_cmd,
    CmdProcessingError,
    MiscHelpers
)
from batchmp.fstools.fsutils import FSH

class FFmpegNotInstalled(Exception):
    def __init__(self, message = None):
        super().__init__(message if message is not None else self.default_message)

    @property
    def default_message(self):
        windows_instructions =  \
        '''
        Installing on Windows:
            http://www.wikihow.com/Install-FFmpeg-on-Windows
            http://www.renevolution.com/how-to-get-ffmpeg-for-windows/
        '''
        macos_instructions =   \
        '''
        Installing on Mac OS X:
            http://www.renevolution.com/how-to-install-ffmpeg-on-mac-os-x/
        '''
        linux_instructions =   \
        '''
        Installing on Ubuntu and Debian:
            $ sudo apt-get update
            $ sudo apt-get install ffmpeg

        Installing on CentOS/RHEL and Fedora:
            enable atrpms repository, then:
            # yum install ffmpeg
        '''

        platforms_install_instructions = ''

        if sys.platform == 'linux':
            platforms_install_instructions = linux_instructions
        elif sys.platform == 'darwin':
            platforms_install_instructions = macos_instructions
        elif sys.platform == 'win32':
            platforms_install_instructions = windows_instructions

        return  \
        '''

        Looks like FFmpeg is not installed

        For full Batch Media Tools Processing functionalty,

        please install FFmpeg and enable it in the command line

        You can download FFmpeg from here:
            http://www.ffmpeg.org/download.html

        Installing FFmpeg
            Manual Install (Universal):
                . download FFmpeg (select a static build)
                . put the FFmpeg executable in your $PATH
        {0}
        '''.format(platforms_install_instructions)

class FFHDefaults:
    DEFAULT_SILENCE_MIN_DURATION = 2
    DEFAULT_SILENCE_NOISE_TOLERANCE = 0.005
    DEFAULT_SILENCE_TARGET_TRIMMED_DURATION = 2

class FFH:
    ''' FFmpeg-related utilities
    '''
    FFEntry = namedtuple('FFEntry', ['path', 'format', 'audio', 'artwork', 'video'])
    FFFullEntry = namedtuple('FFFullEntry', ['path', 'format', 'audio_streams',
                                                            'video_streams', 'artwork_streams'])

    @staticmethod
    def ffmpeg_installed():
        """ Checks if ffmpeg is installed and in system PATH
        """
        ffmpeg_app_name = 'ffmpeg' if os.name != 'nt' else 'ffmpeg.exe'
        for path in os.environ['PATH'].split(os.pathsep):
            app_path = os.path.join(path, ffmpeg_app_name)
            if os.path.isfile(app_path) and os.access(app_path, os.X_OK):
                return True
        return False

    @staticmethod
    def media_file_info(fpath):
        ''' Compact media file info
            Extracts main audio / artwork streams
        '''
        full_entry = FFH.media_file_info_full(fpath)
        if full_entry:
            audio_stream = artwork_stream = video_stream = None
            if full_entry.audio_streams and len(full_entry.audio_streams) > 0:
                # if there are multiple audio streams, take the first
                audio_stream = full_entry.audio_streams[0]

            if full_entry.video_streams and len(full_entry.video_streams) > 0:
                # in case there are multiple art images, take the first
                video_stream = full_entry.video_streams[0]

            if full_entry.artwork_streams and len(full_entry.artwork_streams) > 0:
                # in case there are multiple art images, take the first
                artwork_stream = full_entry.artwork_streams[0]


            return FFH.FFEntry(fpath, full_entry.format, audio_stream, artwork_stream, video_stream)
        else:
            return None

    @staticmethod
    def media_file_info_full(fpath):
        ''' Gathers full info about a media file
        '''
        if not FFH.ffmpeg_installed():
            return None

        cmd = ''.join(('ffprobe ',
                            ' -v quiet',
                            ' -show_streams',
                            #' -select_streams a',
                            ' -show_format',
                            ' -print_format json',
                            ' {}'.format(shlex.quote(fpath))))
        try:
            output, _ = run_cmd(cmd)
        except CmdProcessingError as e:
            return None
        else:
            out = json.loads(output)
            if not out:
                return None

            streams = out.get('streams')
            format = out.get('format')
            audio_streams = video_streams = artwork_streams = None
            if streams:
                is_audio_stream = lambda stream: True if stream.get('codec_type') == 'audio' else False
                is_video_stream = lambda stream: True if (stream.get('codec_type') == 'video' and format.get('format_name') != 'tty') else False

                is_image_stream = lambda stream: True if \
                        stream['codec_name'].lower() in FFH.common_media_extensions(FSMediaEntryType.IMAGE) else False


                audio_streams = [stream for stream in streams if is_audio_stream(stream)]
                video_streams = [stream for stream in streams if \
                                        is_video_stream(stream) and not is_image_stream(stream)]
                artwork_streams = [stream for stream in streams if \
                                        is_video_stream(stream) and is_image_stream(stream)]

            format = out.get('format')
            return FFH.FFFullEntry(fpath, format, audio_streams, video_streams, artwork_streams)

    @staticmethod
    def ffmpeg_supported_media(fpath = None, ffentry = None):
        ''' Determines if a file can be processed with FFmpeg
        '''
        media_type = FFH.media_type(fpath = fpath, ffentry = ffentry)
        return media_type in (FSMediaEntryType.VIDEO, FSMediaEntryType.AUDIO)

    @staticmethod
    def media_type(fpath = None, ffentry = None, fast_scan = False):
        ''' Determines file media type
        '''
        if fast_scan and fpath and not ffentry:
            fpath_ext = FSH.path_extension(fpath)
            if fpath_ext in FFH.common_media_extensions(FSMediaEntryType.IMAGE):
                return FSMediaEntryType.IMAGE
            elif fpath_ext in FFH.common_media_extensions(FSMediaEntryType.AUDIO):
                return FSMediaEntryType.AUDIO
            elif fpath_ext in FFH.common_media_extensions(FSMediaEntryType.VIDEO):
                return FSMediaEntryType.VIDEO
            else:
                return FSMediaEntryType.NONMEDIA

        ffentry = ffentry if ffentry else FFH.media_file_info(fpath)
        if ffentry:
            if hasattr(ffentry, "video")and ffentry.video:
                return FSMediaEntryType.VIDEO
            elif hasattr(ffentry, "audio") and ffentry.audio:
                return FSMediaEntryType.AUDIO
            elif hasattr(ffentry, "artwork") and ffentry.artwork:
                return FSMediaEntryType.IMAGE

        return FSMediaEntryType.NONMEDIA            


    @staticmethod
    def common_media_extensions(media_type):
        media_types_ext_map = {
          FSMediaEntryType.IMAGE: ('jpeg', 'png', 'gif', 'tiff', 'bmp', 'mjpeg', 'jpg'),
          FSMediaEntryType.VIDEO: ('264', 'avi', 'mp4', 'mp4v', 'mpeg', 'mpg', 'mov ', 'mkv', 'webm', 'wmv', 'flv', 'm4v', 'mov'),
          FSMediaEntryType.AUDIO: ('wav', 'mp3', 'ogg', 'flac', 'aiff', 'wma', 'aac', 'mid', 'm4a', 'mka', 'm4b'),
        }
        return media_types_ext_map.get(media_type, None)


    @staticmethod
    def silence_detector(fpath, *,
                                min_duration = FFHDefaults.DEFAULT_SILENCE_MIN_DURATION,
                                noise_tolerance_amplitude_ratio = FFHDefaults.DEFAULT_SILENCE_NOISE_TOLERANCE):
        ''' Detects silence
            If successful, returns a list of SilenceEntry tuples
        '''
        if not FFH.ffmpeg_installed():
            return None

        cmd = ''.join(('ffmpeg',
                            ' -i {}'.format(shlex.quote(fpath)),
                            ' -af silencedetect=',
                            'n={}'.format(noise_tolerance_amplitude_ratio),
                            ':d={}'.format(min_duration),
                            ' -vn',
                            ' -sn',
                            ' -f null - '))

        # print(cmd)
        try:
            output, _ = run_cmd(cmd)
        except CmdProcessingError as e:
            return None
        else:
            silence_starts = re.findall('(?<=silence_start:)(?:\D*)(\d*\.?\d+)', output)
            silence_ends = re.findall('(?<=silence_end:)(?:\D*)(\d*\.?\d+)', output)

            SilenceEntry = namedtuple('SilenceEntry', ['silence_start', 'silence_end'])
            silence_entries = []
            for ss, se in zip(silence_starts, silence_ends):
                silence_entries.append(SilenceEntry(float(ss), float(se)))

            if len(silence_entries) < len(silence_starts):
                # matched non-balanced silence at the end
                # try to parse output audio duration and use it as the silence_end value
                found = re.findall('(?<=Duration:)(?:\D*)([\d:\.]*)', output)
                if found:
                    duration = MiscHelpers.time_delta(found[0]).total_seconds()
                else:
                    duration = float(sys.maxsize)
                silence_entries.append(SilenceEntry(float(silence_starts[-1]), duration))

            return silence_entries

    @staticmethod
    def volume_detector(fpath):
        ''' Detect the volume of input media file
            Returns Mean Volume and Max Volume in decibels, relative to max PCM value
        '''
        if not FFH.ffmpeg_installed():
            return None

        cmd = ''.join(('ffmpeg',
                            ' -i {}'.format(shlex.quote(fpath)),
                            ' -filter:a "volumedetect"',
                            ' -vn',
                            ' -sn',
                            ' -f null - '))
        #print(cmd)
        try:
            output, _ = run_cmd(cmd)
        except CmdProcessingError as e:
            return None
        else:
            mean_volume = max_volume = 0

            # mean volume
            found = re.findall('(?<=mean_volume:)(?:\D*)(\d*\.?\d+)', output)
            if found:
                mean_volume = float(found[0])

            # max volume
            found = re.findall('(?<=max_volume:)(?:\D*)(\d*\.?\d+)', output)
            if found:
                max_volume = float(found[0])

            VolumeEntry = namedtuple('VolumeEntry', ['mean_volume', 'max_volume'])
            return VolumeEntry(mean_volume, max_volume)


# Quick dev test
if __name__ == '__main__':
    print(FFmpegNotInstalled().default_message)

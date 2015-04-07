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
from functools import wraps
from collections import namedtuple
import batchmp.fstools.fsutils as fsutils
from batchmp.commons.utils import (
    run_cmd,
    CmdProcessingError
)

class FFmpegNotInstalled(Exception):
    def __init__(self, message = None):
        super().__init__(message if message is not None else self.default_message)

    @property
    def default_message(self):
        windows_instructions =  '''
        Installing FFmpeg on Windows:
            http://www.renevolution.com/how-to-get-ffmpeg-for-windows/
            http://www.wikihow.com/Install-FFmpeg-on-Windows
                                '''
        macos_instructions =    '''
        Installing FFmpeg on Mac OS X:
            http://www.renevolution.com/how-to-install-ffmpeg-on-mac-os-x/
                                '''
        linux_instructions =    '''
        Installing FFmpeg on Ubuntu and Debian:
            $ sudo apt-get update
            $ sudo apt-get install ffmpeg

        Installing FFmpeg on CentOS/RHEL and Fedora:
            enable atrpms repository, then:
            # yum install ffmpeg
                                '''
        install_instructions = ''

        if sys.platform == 'linux':
            install_instructions = linux_instructions
        elif sys.platform == 'darwin':
            install_instructions = macos_instructions
        elif sys.platform == 'win32':
            install_instructions = windows_instructions

        return  '''

        Looks like FFmpeg is not installed

        For full Batch Media Tools Processing functionalty,

        please install FFmpeg and enable it in the command line

        You can download FFmpeg from here:
            http://www.ffmpeg.org/download.html
        {0}
        '''.format(install_instructions)


class FFH:
    ''' FFmpeg-related utilities
    '''
    FFEntry = namedtuple('FFEntry', ['path', 'format', 'audio', 'artwork'])
    FFFullEntry = namedtuple('FFFullEntry', ['path', 'format', 'audio_streams', 'video_streams'])

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
            Extracts key information relevant for futher processing,
            such as main audio stream, artwork, etc.
        '''
        full_entry = FFH.media_file_info_full(fpath)
        if full_entry:
            audio_stream = artwork_stream = None
            if full_entry.audio_streams and len(full_entry.audio_streams) > 0:
                # if there are multiple audio streams, take the first
                audio_stream = full_entry.audio_streams[0]
            else:
                return None

            artwork_streams = [stream for stream in full_entry.video_streams
                                        if 'codec_type' in stream and stream['codec_type'] == 'video'
                                            and stream['codec_name'].lower() in ('jpeg', 'png', 'gif', 'tiff', 'bmp')]
            if artwork_streams:
                # in case there are multiple art images, take the first
                artwork_stream = artwork_streams[0]

            return FFH.FFEntry(fpath, full_entry.format, audio_stream, artwork_stream)
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
                            ' "{}"'.format(fpath)))
        try:
            output, _ = run_cmd(cmd)
        except CmdProcessingError as e:
            return None
        else:
            out = json.loads(output)
            if not out:
                return None

            streams = out.get('streams')
            audio_streams = video_streams = None
            if streams:
                audio_streams = [dict for dict in streams
                                                if 'codec_type' in dict and
                                                    dict['codec_type'] == 'audio']
                video_streams = [dict for dict in streams
                                            if 'codec_type' in dict and
                                                    dict['codec_type'] == 'video']
            format = out.get('format')

            return FFH.FFFullEntry(fpath, format, audio_streams, video_streams)

    @staticmethod
    def supported_media(fpath):
        ''' Determines if a file can be processed with FFmpeg
        '''
        if not FFH.media_file_info(fpath):
            return False
        else:
            return True

    @staticmethod
    def media_files(src_dir,
                    start_level = 0, end_level = sys.maxsize,
                    include = None, exclude = None,
                    filter_dirs = True, filter_files = True, pass_filter = None):
        """ Return a generator of media files that are supported by FFmpeg
        """
        if not pass_filter:
            pass_filter = lambda fpath: FFH.supported_media(fpath)

        media_files = (entry.realpath for entry in fsutils.DWalker.file_entries(src_dir,
                                                        start_level = start_level, end_level = end_level,
                                                        include = include, exclude = exclude,
                                                        filter_dirs = filter_dirs, filter_files = filter_files,
                                                        pass_filter = pass_filter))
        return media_files

    @staticmethod
    def silence_detector(fpath, *,
                                min_duration = 2,
                                noise_tolerance_amplitude_ratio = 0.001):
        ''' Detects silence
            If successful, returns a list of SilenceEntry tuples
        '''
        if not FFH.ffmpeg_installed():
            return None

        cmd = ''.join(('ffmpeg',
                            ' -i "{}"'.format(fpath),
                            ' -af silencedetect=',
                            'n={}'.format(noise_tolerance_amplitude_ratio),
                            ':d={}'.format(min_duration),
                            ' -f null - '))
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
                silence_entries.append(SilenceEntry(ss, se))

            if len(silence_entries) < len(silence_starts):
                # matched silence at the end
                silence_entries.append(SilenceEntry(silence_starts[-1], str(float(sys.maxsize))))

            return silence_entries


'''
if __name__ == '__main__':
    url = "https://dl-web.dropbox.com/get/11%20Quick%20Shares/art.png?_subject_uid=2573652&w=AADC6woSGldkSToPIgp7dBhLruvSxL9isOlMxEmRYa9cZQ"
    #url = 'http://ecx.images-amazon.com/images/I/51kmgZ58H9L._SY300_.jpg'
    #url = 'google.com'
    art = load_image_from_url2(url)

    if art:
        target_art_path = '/Users/AKPower/Desktop/art.png'
        with open(target_art_path, 'wb') as f:
            f.write(art)



    silence_entries = FFH.silence_detector('/Users/AKPower/Desktop/_Rips/Chopin Etudes/12 Vladimir Ashkenazy - 12 Etudes Op. 25 - No. 11 in A minor, No. 12 in C minor.m4a',
                         min_duration = 2,
                         noise_tolerance_amplitude_ratio = 0.001)
    print(silence_entries)

'''

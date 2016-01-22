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


import os, re
from batchmp.ffmptools.utils.cuesheet import CueSheet, CueTrack

class CueParseReadDataEncodingError(Exception):
    def __init__(self, message = None):
        super().__init__(message if message is not None else self.default_message)

    @property
    def default_message(self):
        return '\n\tUnable to read data from the .cue file' \
               '\n\tProvide correct encoding argument when parsing files, e.g.:' \
               '\n\t\tcue_parser = CueParser()' \
               '\n\t\tcue_parser.parse(cue_filepath, encoding = "latin-1")'

class CueLineParser:
    ''' Cue Lines Parser
    '''
    def __init__(self):
        self._line_matcher = re.compile('^([A-Z]+)\s+(.*)$')

    def parse_line(self, line):
        ''' Parses a line read from a *.cue file
        '''
        line = line.strip()

        command = params = None
        match = self._line_matcher.match(line)
        if match and len(match.groups()) >= 2:
            command = match.group(1)
            params = self._parse_params(match.group(2))

        return command, params

    def _parse_params(self, params):
        res = []
        params = params.strip()
        if params:
            quote_idx = params.find('"')
            if quote_idx < 0:
                for param in params.split():
                    res.append(param)
            elif quote_idx == 0:
                if len(params) > 1:
                    res = self._parse_params(params[quote_idx + 1:])
            elif quote_idx > 0:
                res.append(params[:quote_idx])
                if len(params) > 1:
                    res = res + self._parse_params(params[quote_idx + 1:])
        return res

class CueParser:
    ''' Cue files parser
    '''
    def __init__(self):
        self._commands_map = {
                            'CATALOG':    self._parse_catalog,
                            'CDTEXTFILE': self._parse_cdtextfile,
                            'FILE':       self._parse_file,
                            'FLAGS':      self._parse_flags,
                            'INDEX':      self._parse_index,
                            'ISRC':       self._parse_isrc,
                            'PERFORMER':  self._parse_performer,
                            'POSTGAP':    self._parse_postgap,
                            'PREGAP':     self._parse_pregap,
                            'REM':        self._parse_rem,
                            'SONGWRITER': self._parse_songwriter,
                            'TITLE':      self._parse_title,
                            'TRACK':      self._parse_track
                            }

        self._time_offset_matcher = re.compile('^(\d{1,3}):(\d{1,2}):(\d{1,2})$')
        self._line_parser = CueLineParser()
        self._lines = None
        self._cuesheet = None

    def parse(self, filepath, encoding = 'utf-8'):
        try:
            self._read_data(filepath, encoding = encoding)
        except CueParseReadDataEncodingError:
            raise
        self._cuesheet = CueSheet()

        for line in self._lines:
            command, params = self._line_parser.parse_line(line)
            if command:
                self._commands_map[command](params)

        return self._cuesheet


    # Internal processing
    #####################
    def _read_data(self, filepath, encoding):
        if not os.path.isfile(filepath):
            print('Cannot open file: {}'.format(filepath))
            exit(2)
        try:
            with open(filepath, encoding = encoding) as f:
                lines = f.read()
        except UnicodeDecodeError:
            raise CueParseReadDataEncodingError
        self._lines = lines.splitlines()

    def _parse_catalog(self, params):
        self._cuesheet.catalog = params[0];

    def _parse_cdtextfile(self, params):
        self._cuesheet.cdtextfile = params[0];

    def _parse_file(self, params):
        self._cuesheet.add_file()
        self._cuesheet.last_file.name = params[0];
        self._cuesheet.last_file.type = params[1];

    def _parse_flags(self, params):
        track = _cuesheet.last_track()
        if track:
            track.flags = params[0]

    def _parse_index(self, params):
        number = int(params[0])
        time_offset = self._parse_time_offset(params[1])

        track = self._cuesheet.last_track
        if track:
            index = CueTrack.Index(number, time_offset)
            track.indexes.append(index)

            # for the first index, look to calculate previous track duration
            if len(track.indexes) == 1:
                penultimate_track = self._cuesheet.penultimate_track
                if penultimate_track and penultimate_track.indexes:
                    time_offset = track.indexes[0].time_offset_timedelta
                    previosOffset = penultimate_track.indexes[0].time_offset_timedelta
                    penultimate_track.duration = time_offset - previosOffset

    def _parse_isrc(self, params):
        track = self._cuesheet.last_track
        if track:
            track.isrc = params[0]

    def _parse_performer(self, params):
        track = self._cuesheet.last_track
        if not track:
            self._cuesheet.performer = params[0]
        else:
            track.performer = params[0]

    def _parse_postgap(self, params):
        track = self._cuesheet.last_track
        if track:
            track.postgap = self._parse_time_offset(params[0])

    def _parse_pregap(self, params):
        track = self._cuesheet.last_track
        if track:
            track.pregap = self._parse_time_offset(params[0])

    def _parse_rem(self, params):
        self._cuesheet.rem.append(' '.join(params))

    def _parse_songwriter(self, params):
        track = self._cuesheet.last_track
        if not track:
            self._cuesheet.songWriter = params[0]
        else:
            track.songWriter = params[0]

    def _parse_title(self, params):
        track = self._cuesheet.last_track
        if not track:
            self._cuesheet.title = params[0]
        else:
            track.title = params[0]

    def _parse_track(self, params):
        number = int(params[0])
        type = params[1]
        self._cuesheet.add_track(number, type)

    def _parse_time_offset(self, time_offset_str):
        mins = secs = frames = 0
        match = self._time_offset_matcher.match(time_offset_str)
        if match:
            mins = int(match.group(1))
            secs = int(match.group(2))
            frames = int(match.group(3))
        time_offset = CueTrack.TimeOffset(mins, secs, frames)
        return time_offset

from datetime import timedelta
if __name__ == '__main__':
    cue_filepath = os.path.expanduser('~/_Dev/GitHub/batch-mp-tools/tests/ffmp/.data/bmfp_a/noise.cue')

    line_parser = CueLineParser()
    param_dict = ['TRACK 01 AUDIO',
              'INDEX 01 00:00:00',
              'TITLE "BMFP Noisy Classical"',
              'FILE "01 background noise.aiff" AIFF',
              'REM GENRE "NOISY CLASSICAL"','REM DATE "2016"']

    for params in param_dict:
        param = line_parser.parse_line(params)
        print(param)
    print()

    parser = CueParser()
    cuesheet = parser.parse(cue_filepath)
    print(cuesheet)




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


import sys, os, re, math
from collections import namedtuple
from enum import Enum
from datetime import timedelta
from string import Template
from batchmp.commons.descriptors import PropertyDescriptor


class CueDefaultOutputDescriptor(PropertyDescriptor):
    ''' Output format property descriptor, with support for default values
    '''
    def __init__(self, func_name):
        self._func_name = func_name

    def __get__(self, instance, type=None):
        value = super().__get__(instance, type = type)
        if not value:
            value = getattr(instance, self._func_name)()
        return value

class TimeOffsetPropertyDescriptor(PropertyDescriptor):
    ''' Named tuple type property descriptor
        or, "typing like a duck rhymes with ..."
    '''
    def __set__(self, instance, value):
        if isinstance(value, tuple): #and hasattr ...
            super().__set__(instance, value)
        else:
            raise TypeError("Not a Tuple Type: {}".format(value))

class CueBase:
    ''' Base cue sheet / track stuff
    '''
    performer = PropertyDescriptor()
    songwriter = PropertyDescriptor()
    title = PropertyDescriptor()
    outputformat = CueDefaultOutputDescriptor("default_output_format")
    substitute_dictionary = CueDefaultOutputDescriptor("default_substitute_dictionary")

    # Internal methods
    ###################
    def __repr__(self):
        template = Template(self.default_output_format)
        return template.safe_substitute(self.default_substitute_dictionary)

    @property
    def default_output_format(self):
        return None

    @property
    def default_substitute_dictionary(self):
        ''' common default output-related template processing
            subclasses can extend this via adding ther specific stuff to process
        '''
        sd = {}
        sd['performer'] = self.performer if self.performer else ''
        sd['songwriter'] = self.songwriter if self.songwriter else ''
        sd['title'] = self.title if self.title else ''

        return sd

class CueTrack(CueBase):
    ''' Cue track attributes / processing
    '''
    TimeOffset = namedtuple('TimeOffset', ['mins', 'secs', 'frames'])
    class Index:
        number = PropertyDescriptor()
        time_offset = TimeOffsetPropertyDescriptor()

        def __init__(self, number, time_offset):
            self.number = number
            self.time_offset = time_offset

        @property
        def time_offset_str(self):
            return '{0:02d}:{1:02d}:{2:02d}'.format(self.time_offset.mins, self.time_offset.secs, self.time_offset.frames)

        @property
        def time_offset_timedelta(self):
            ''' time_offset is specified as mm:ss:ff (minute-second-frame) format,
                where there are 75 such frames per second of audio
            '''
            seconds = self.time_offset.secs + self.time_offset.frames / 75
            return timedelta(minutes = self.time_offset.mins, seconds = seconds)

        @property
        def time_offset_in_seconds(self):
            return self.time_offset_timedelta.total_seconds()

    number = PropertyDescriptor()
    type =  PropertyDescriptor()
    flags = PropertyDescriptor()
    isrc = PropertyDescriptor()
    pregap  = TimeOffsetPropertyDescriptor()
    postgap = TimeOffsetPropertyDescriptor()
    duration = PropertyDescriptor()

    def __init__(self, number, type):
        self.number = number
        self.type = type
        self.indexes = []

    @property
    def offset_in_seconds(self):
        offset_in_seconds = 0
        if len(self.indexes) > 0:
            offset_in_seconds = self.indexes[0].time_offset_in_seconds
        return offset_in_seconds

    @property
    def duration_in_seconds(self):
        return self.duration.total_seconds() if self.duration else 0

    # Internal methods
    ###################
    @property
    def default_output_format(self):
        return '  $number\t$time_offset\t$duration\t$title'

    @property
    def default_substitute_dictionary(self):
        ''' cue track default output template processing
        '''
        sd = super().default_substitute_dictionary
        if len(self.indexes) > 0:
            sd['time_offset'] = self.indexes[0].time_offset_str
        else:
            sd['time_offset'] = ''

        sd['number'] = '{0:02d}'.format(self.number) if self.number else ''
        if self.duration:
            minutes = math.floor(self.duration.total_seconds() / 60)
            sd['duration'] = '{0:02d}:{1:02d}'.format(minutes, self.duration.seconds - 60 * minutes)
        else:
            sd['duration'] = '  :  '
        return sd

class CueSheet(CueBase):
    ''' Cue sheet processing
    '''
    class File:
        name = PropertyDescriptor()
        format = PropertyDescriptor()

        def __init__(self):
            self.tracks = []

    catalog = PropertyDescriptor()
    cdtextfile = PropertyDescriptor()

    def __init__(self):
        self.files = []
        self.rem = []

    @property
    def last_file(self):
        files_cnt = len(self.files)
        if files_cnt > 0:
            return self.files[files_cnt - 1]
        return None

    @property
    def last_track(self):
        file = self.last_file
        if file and file.tracks:
            tracks_cnt = len(file.tracks)
            if tracks_cnt > 0:
                return file.tracks[tracks_cnt - 1]
        return None

    @property
    def penultimate_track(self):
        file = self.last_file
        if file and file.tracks:
            tracks_cnt = len(file.tracks)
            if tracks_cnt > 1:
                return file.tracks[tracks_cnt - 2]
        return None

    def add_file(self):
        file = CueSheet.File()
        self.files.append(file)

    def add_track(self, number, type):
        file = self.last_file
        if file:
            file.tracks.append(CueTrack(number, type))

    # Internal methods
    ###################
    @property
    def default_output_format(self):
        return 'Performer: $performer\nTitle: $title\nRem: $rem\nFiles: $files\nTracks: $tracks'

    @property
    def default_substitute_dictionary(self):
        ''' cue sheet default output template processing
        '''
        sd = super().default_substitute_dictionary

        if self.rem:
            rem_output = '\n'
            for rem in self.rem:
                if rem == self.rem[-1]:
                    rem_output += ' {}'.format(rem)
                else:
                    rem_output += ' {}\n'.format(rem)
            sd['rem'] = rem_output

        files_output = '\n'
        tracks_output = '\n'
        for file in self.files:
            if file == self.files[-1]:
                files_output += ' {0} ({1})'.format(file.name, file.type)
            else:
                files_output += ' {0} ({1})\n'.format(file.name, file.type)
            for track in file.tracks:
                tracks_output += '{}\n'.format(str(track))

        sd['files'] = files_output
        sd['tracks'] = tracks_output

        return sd


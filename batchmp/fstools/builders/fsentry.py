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


from enum import IntEnum

class FSEntry:
    ''' File System entry representation
    '''
    def __init__(self, type, basename, realpath, indent, 
                    isEnclosingEntry = False, isEnclosingFilesContainterEntry = False,
                    isScopeSwitchingEntry = False):
        self.type = type
        self.basename = basename
        self.realpath = realpath
        self.indent = indent
        self.isEnclosingEntry = isEnclosingEntry
        self.isEnclosingFilesContainterEntry = isEnclosingFilesContainterEntry
        self.scopeSwitchingEntry = isScopeSwitchingEntry


class FSEntryType(IntEnum):
    ROOT =  0x00000
    DIR  =  0x00001
    FILE =  0x00002


class FSMediaEntryType(IntEnum):
    IMAGE       =  0x00010
    AUDIO       =  0x00011
    VIDEO       =  0x00012
    NONMEDIA    =  0x00013


class FSMediaEntryGroupType(IntEnum):
    MEDIA       =  0x00100
    PLAYABLE    =  0x00101
    NONPLAYABLE =  0x00102    
    ANY         =  0x00103


class FSEntryDefaults:    
    DEFAULT_NESTED_INDENT = '  '
    DEFAULT_INCLUDE = '*'
    DEFAULT_EXCLUDE = '.*' #exclude hidden files
    DEFAULT_SORT = 'na'
    DEFAULT_FILE_TYPE = 'any'
    DEFAULT_MEDIA_TYPE = 'playable'



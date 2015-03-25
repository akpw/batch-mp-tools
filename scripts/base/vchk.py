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

''' Python version check
'''

from __future__ import print_function
import sys

def check_version():
    if sys.version_info.major < 3:
        print('''
            Batch Media Processing Tools require Python version 3.4 or later.

            You can create an isolated Python 3.4 environment using the virtualenv tool
            (http://docs.python-guide.org/en/latest/dev/virtualenvs/)

            ''')
        sys.exit(1)
    elif sys.version_info.major == 3 and sys.version_info.minor < 4:
        print('''

            Batch Media Processing Tools require Python version 3.4 or later.
            Please upgrade to the latest Python 3.x version.

            ''')
        sys.exit(1)

# check
check_version()

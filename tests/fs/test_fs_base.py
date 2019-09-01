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
from batchmp.ffmptools.ffutils import run_cmd
from ..base import test_base

class FSTest(test_base.BMPTest):
    @classmethod
    def setUpClass(cls):
        cls.src_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), 'data'))
        cls.bckp_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '.data'))
        super(FSTest, cls).setUpClass()

    def get_last_digit_from_shell_cmd(self, cmd):
        cmd_output, _ = run_cmd(cmd, shell = True)
        p = re.compile('(\d+)(?!.*\d)')
        match = p.search(cmd_output)
        if match:
            return int(match.group())
        else:
            return -1

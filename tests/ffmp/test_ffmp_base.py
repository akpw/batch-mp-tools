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

import os
from ..base import test_base

class FFMPTest(test_base.BMPTest):
    @classmethod
    def setUpClass(cls):
        cls.src_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), 'data'))
        cls.bckp_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '.data'))
        super(FFMPTest, cls).setUpClass()

    def setUp(self):
        self.media_info = {'00 Background noise.mp3': 6,
                           '01 Background noise.mp4': 116,
                           '02 Background noise.mp4': 175}

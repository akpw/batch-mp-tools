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

import datetime, math
from batchmp.ffmptools.ffmputils import FFH, timed

""" Base FFMPCommandBuilder
"""

class FFMPCommandRunner:
    def __init__(self):
        if not FFH.ffmpeg_installed():
            raise utils.FFmpegNotInstalled('\n\tLooks like ffmpeg is not installed'
                                           '\n\tCheck it out here:'
                                           ' http://www.ffmpeg.org/download.html\n')
    @timed
    def run(self, *args, **kwargs):
        pass

    def run_report(self, cpu_core_time, total_elapsed):
        ttd = datetime.timedelta(seconds = math.ceil(total_elapsed))
        ctd = datetime.timedelta(seconds = math.ceil(cpu_core_time))
        print('Total running time: {}'.format(str(ttd)))
        print('Cumulative CPU Cores time: {}'.format(str(ctd)))



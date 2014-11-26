#!/usr/bin/env python
# coding=utf8
## Copyright (c) 2014 Arseniy Kuznetsov
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

import datetime
from argparse import ArgumentParser
from batchmp.ffmptools.ffmp import FFMP

""" Reduces background audio noise in media files via filtering out highpass / low-pass frequencies
      . Processes all media files in a source directory, when recursive (-r) also goes to subfolders
      . Supports multiple processing passes
      . Leverage Python multiprocessing to utilize available CPU cores
      . Supports backing up original media files within respective folders
      . Displays continuos progress

    Usage: denoiser.py -d DIR [-r] [-n NUM_PASSES] [-hp HIGH_PASS] [-lp LOW_PASS] [-nb] [-q] [-h]

    Unless specified, the script uses the following defaults:
      . High-pass filter:   200
      . Low-pass filter:    3000
      . Recursive:          False
      . Number of passes:   1
      . No backups:         False
      . Quiet:              False
"""

def parse_options():
    parser = ArgumentParser(description = 'Reduces background audio noise in media files via filtering out highpass / low-pass frequencies')
    parser.add_argument("-d", "--dir",
                required=True,
                help = "Source directory")
    parser.add_argument("-r", "--recursive",
                help = "Recursive processing",
                action='store_true')
    parser.add_argument("-n", "--num-passes",
                help = "Applies filters in multiple passes",
                type = int,
                default = 1)
    parser.add_argument("-nb", "--no-b",
                help = "Disables backups",
                action='store_true')
    parser.add_argument("-q", "--quiet",
                help = "Does not show info messages during processing",
                action='store_true')

    group = parser.add_argument_group('pass filters')
    group.add_argument("-hp", "--high-pass",
                help = "Cutoff boundary for lower frequencies",
                type = int,
                default = 200)
    group.add_argument("-lp", "--low-pass",
                help = "Cutoff boundary for higher frequencies",
                type = int,
                default = 3000)
    return vars(parser.parse_args())

def main():
  args = parse_options()

  ffmp = FFMP(args['dir'])
  cpu_core_time, total_elapsed = ffmp.apply_af_filters(
                                          num_passes=args['num_passes'],
                                          recursive = args['recursive'],
                                          highpass=args['high_pass'],
                                          lowpass=args['low_pass'],
                                          backup=not args['no_b'],
                                          quiet=args['quiet'])

  ttd = datetime.timedelta(seconds=total_elapsed)
  ctd = datetime.timedelta(seconds=cpu_core_time)
  print('All done in: {}'.format(str(ttd)[:10]))
  print('FFmpeg CPU Cores time: {}'.format(str(ctd)[:10]))

if __name__ == '__main__':
    main()


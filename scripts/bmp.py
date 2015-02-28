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


from batchmp.ffmptools.ffcommands.denoise import Denoiser
from scripts.base.bmpbargp import BMPBaseArgParser

""" Batch processing of media files
      . Uses multiprocessing to utilize available CPU cores
      . supports source directory / source file modes
      . supports recursion to specified end_level
      . allows for include / exclude patterns (Unix style)
      . action commands:
          .. denoise
          .. split
          .. speed up
          .. slow down
          .. adjust volume
          .. convert

    Usage: bmp [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
      Global Options (bmp -h for additional help)
        [-e END_LEVEL]                        End level for recursion into nested folders
        [-i INCLUDE] [-e EXCLUDE]             Include names pattern
        [-fd FILTER_DIRS] [-ff FILTER_FILES]  Use Include/Exclude patterns on dirs / files
        [-s SORT]                             Sorting for files / folders
        [-q QUIET]                            Do not visualise / show messages during processing

      Commands: (bmp {command} -h for additional help)
      {denoise, split, speedup, slowdown, volume, convert}
        denoise   Reduces background audio noise in media files
                      via filtering out highpass / low-pass frequencies
        split     TDB: Splits media files
        speedup   TDB: Uses Time Stretching to increase audio / video speed
        slowdown  TDB: Uses Time Stretching to decrease audio / video speed
        volume    TDB: Adjust audiot volume
        convert   TDB: Convert media to specified format

      bmp {Command} -h for additional help
"""

class BMPArgParser(BMPBaseArgParser):
    @staticmethod
    def parse_commands(parser):
        # Commands
        subparsers = parser.add_subparsers(help = 'BMP commands',
                                            dest='sub_cmd', title = 'BMP Commands')

        # Denoise
        denoise_parser = subparsers.add_parser('denoise', help = 'Reduces background audio noise in media files via filtering out highpass / low-pass frequencies')
        denoise_parser.add_argument('-np', '--numpasses', dest='num_passes',
                help = 'Applies filters in multiple passes',
                type = int,
                default = 1)
        denoise_parser.add_argument("-nb", "--no-backup", dest='nobackup',
                    help = "Disables backups",
                    action='store_true')

        group = denoise_parser.add_argument_group('Pass Filters')
        group.add_argument("-hp", "--highpass", dest='highpass',
                    help = "Cutoff boundary for lower frequencies",
                    type = int,
                    default = 200)
        group.add_argument("-lp", "--lowpass", dest='lowpass',
                    help = "Cutoff boundary for higher frequencies",
                    type = int,
                    default = 3000)


    @staticmethod
    def check_args(args):
        BMPBaseArgParser.check_args(args)

        if not args['sub_cmd']:
            args['sub_cmd'] = 'denoise'
            args['nobackup'] = False
            args['numpasses'] = 1
            args['highpass'] = 200
            args['lowpass'] = 3000


class BMPDispatcher:
    @staticmethod
    def denoise(args):
        Denoiser().apply_af_filters(src_dir = args['dir'],
                sort = args['sort'], end_level = args['end_level'], quiet=args['quiet'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = not args['filter_dirs'], filter_files = not args['filter_files'],
                num_passes=args['numpasses'], highpass=args['highpass'], lowpass=args['lowpass'],
                backup=not args['nobackup'])


    @staticmethod
    def dispatch():
        args = BMPArgParser().parse_options(script_name = 'bmp')

        if args['sub_cmd'] == 'denoise':
            BMPDispatcher.denoise(args)

def main():
    BMPDispatcher.dispatch()

if __name__ == '__main__':
    main()



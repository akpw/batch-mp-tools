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

import unittest, sys
from test_ffmp_tools import FFMPTests
from test_ffmp_utils import FFMPUtilsTests

if __name__ == '__main__':
    ''' Runs all relevant tests
    '''
    if sys.version_info >= (3, 0):
        test_classes_to_run = [FFMPTests, FFMPUtilsTests]

        loader = unittest.TestLoader()

        suites_list = []
        for test_class in test_classes_to_run:
            suite = loader.loadTestsFromTestCase(test_class)
            suites_list.append(suite)

        big_suite = unittest.TestSuite(suites_list)

        runner = unittest.TextTestRunner()
        results = runner.run(big_suite)

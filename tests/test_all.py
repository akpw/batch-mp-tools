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

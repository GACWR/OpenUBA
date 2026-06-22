'''
Copyright (c) 2019–present Georgia Cyber Warfare Range
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
# TODO: REMOVE THIS FILE AS EACH MODULE HAS A _test.py file

import unittest

from dataset_test import DatasetCSVLocationTestCase, DatasetSessionDataFrameShapeTestCase
from process_test import DataSourceTestCase

'''
@description everything in Dataset File
'''
class DatasetTest():
    @staticmethod
    def Run():
        # dataset related file
        test_cases = [
                        DatasetCSVLocationTestCase,
                        DatasetSessionDataFrameShapeTestCase,
                        DataSourceTestCase
                     ]

        for test_class in test_cases:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            unittest.TextTestRunner(verbosity=2).run(suite)


class Test():
    @staticmethod
    def Run():
        DatasetTest.Run()

'''
Copyright 2019-Present The OpenUB Platform Authors
This file is part of the OpenUB Platform library.
The OpenUB Platform is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
The OpenUB Platform is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License
along with the OpenUB Platform. If not, see <http://www.gnu.org/licenses/>.
'''


import unittest
from dataset_test import DatasetTestCase, DatasetSessionTestCase

'''
@description everything in Dataset File
'''
class DatasetTest():
    @staticmethod
    def Run():

        # dataset related file
        test_cases = [DatasetTestCase,DatasetSessionTestCase]
        for test_class in test_cases:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            unittest.TextTestRunner(verbosity=2).run(suite)


class Test():
    @staticmethod
    def Run():
        DatasetTest.Run()

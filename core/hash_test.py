'''
Copyright 2019-Present The OpenUBA Platform Authors
This file is part of the OpenUBA Platform library.
The OpenUBA Platform is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
The OpenUBA Platform is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License
along with the OpenUBA Platform. If not, see <http://www.gnu.org/licenses/>.
'''



import unittest
from hash import Hash, HashData, HashFile, HashLargeFile

'''
@name HashTestCase
@description this is the test case for all User classes
'''
class HashTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_hash(self):
        starting_string: str = "test"
        expected_result = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        data_hasher = HashData(starting_string.encode())
        self.assertEqual(data_hasher.result, expected_result)

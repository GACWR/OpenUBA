'''
Copyright (c) 2019–present GACWR
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
import unittest
from core.hash import Hash, HashData, HashFile, HashLargeFile

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

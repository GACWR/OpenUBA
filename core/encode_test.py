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
import unittest
from core.encode import Base64, B64EncodeFile, B64DecodeFile

'''
@name EncodeTestCase
@description this is the test case for all User classes
'''
class EncodeTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_base64_encode(self):
        starting_string: str = "test"
        expected_result = b"dGVzdA=="
        encoded_string = Base64().encode(starting_string)
        self.assertEqual(encoded_string, expected_result)

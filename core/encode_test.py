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
from encode import Base64, B64EncodeFile, B64DecodeFile

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

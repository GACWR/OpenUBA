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
import pandas as pd
from process import DataSource, DataSourceFileType
import logging
from typing import Dict, Tuple, Sequence, List
from unittest.mock import MagicMock

'''
@name DataSourceTestCase
@description this is the test case for Data Source
'''
class DataSourceTestCase(unittest.TestCase):
    def setUp(self):
        self.datasource = DataSource()

    def test_csv_init(self):
        self.assertEqual(self.datasource.data_source_string(DataSourceFileType.CSV), "csv")


'''
@name 
@description
'''

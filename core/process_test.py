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
import pandas as pd
from core.process import DataSource, DataSourceFileType
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
        self.assertEqual(DataSourceFileType.CSV.value, "csv")


'''
@name
@description
'''

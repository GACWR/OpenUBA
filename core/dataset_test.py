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
import pandas as pd
from core.dataset import *
import logging
from typing import Dict, Tuple, Sequence, List


from unittest.mock import MagicMock

'''
@name DatasetCSVLocationTestCase
@description this is the test case for dataset session csv location
'''
class DatasetCSVLocationTestCase(unittest.TestCase):
    def setUp(self):
        self.parent_folder = "parent_folder"
        self.folder = "folder"
        self.location_type = "location type"
        self.csv = CSV(self.parent_folder,
                       self.folder,
                       self.location_type,
                       ",")

    def test_csv_init(self):
        self.assertEqual(self.csv.file_location,
                         self.parent_folder+"/"+self.folder)

'''
@name DatasetSessionDataFrameShapeTestCase
@description all unit tests for DatasetSession dataframe get shape
'''
class DatasetSessionDataFrameShapeTestCase(unittest.TestCase):
    def setUp(self):
         self.dataset_session = DatasetSession("csv")
         self.dataset_session.csv_dataset = CSV("", "", "", "")
         df = pd.DataFrame([("a"),("1")])
         #get_dataframe = MagicMock(return_value=DataFrame(df))
         self.dataset_session.csv_dataset.dataframe = CoreDataFrame(df)

    def test_read_csv(self):
        self.assertTrue(isinstance(self.dataset_session.get_csv_dataset().get_dataframe().data,
                                   pd.core.frame.DataFrame))

    def test_get_size(self):
        self.assertEqual(self.dataset_session.get_csv_size(), (2,1))


'''
@name
@description
'''

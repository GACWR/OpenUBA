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
from dataset import *
import logging
from typing import Dict, Tuple, Sequence, List


from unittest.mock import MagicMock

'''
@name DatasetTestCase
@description this is the test case for all Dataset classes
'''
class DatasetTestCase(unittest.TestCase):
    def setUp(self):
        self.parent_folder = "parent_folder"
        self.folder = "folder"
        self.location_type = "location type"
        self.csv = CSV(self.parent_folder,
                       self.folder,
                       self.location_type)
    def test_csv_init(self):
        self.assertEqual(self.csv.file_location,
                         self.parent_folder+"/"+self.folder)

'''
@name DatasetSessionTestCase
@description all unit tests for DatasetSession class
'''
class DatasetSessionTestCase(unittest.TestCase):
    def setUp(self):
         self.dataset_session = DatasetSession("csv")
         self.dataset_session.dataset = CSV("", "", "")
         df = pd.DataFrame([("a"),("1")])
         #get_dataframe = MagicMock(return_value=DataFrame(df))
         self.dataset_session.dataset.dataframe = CoreDataFrame(df)

    def test_read_csv(self):
        self.assertTrue(isinstance(self.
                                   dataset_session.
                                   get_dataset().
                                   get_dataframe().
                                   data,
                                   pd.core.frame.DataFrame))

    def test_get_size(self):
        self.assertEqual(self.dataset_session.get_size(), (2,1))

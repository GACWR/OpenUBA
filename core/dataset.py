'''
Copyright 2019-Present The OpenUEBA Platform Authors
This file is part of the OpenUEBA Platform library.
The OpenUEBA Platform is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
The OpenUEBA Platform is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License
along with the OpenUEBA Platform. If not, see <http://www.gnu.org/licenses/>.
'''

'''
@name dataset
@description purposed with dataset management, and interaction
'''

import logging
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Sequence, List



'''
@name PreSplitRecord
@description before split_record
'''

class PreSplitRecord:
    def __init__(self, function):
        logging.info("PreSplitRecord constructor")
        self.function = function

    def __call__(self, *args) -> List:
        logging.warning("PreSplitRecord")
        logging.error("PreSplitRecord args: "+str(args))
        logging.warning("PreSplitRecord args len: "+str(len(args)))
        record: str = args[0]
        sep: str = args[1]
        parser_result: list = self.function(args[0], record, sep)
        return parser_result




'''
@name Parser
@description parse raw dataset to cleaneddataset
'''
class Parser():
    def __init__(self):
        logging.info("Parser init: "+str(self))

    '''
    @name split_record
    @description, take in a record/row, and
    return an list of strings. @static because we only need one, and
    we don't need to keep a parser object in memory
    '''
    #@staticmethod
    @PreSplitRecord
    def split_record(self, record: str, sep: str) -> List:
        logging.info("splitting record")
        split_result = record.split(sep)
        logging.warning("split record: "+str(split_result))
        return split_result


class DataFrame():
    def __init__(self, df):
        self.data = df

'''
@name DatasetPrior
@description take beh
'''
class DatasetLogPrior:
    def __init__(self, function):
        self.function = function

    '''
    @name DatasetLogPrior.__call__
    @description call before read_from_disk, after dataframe is
    assigned to class's public memory
    '''
    def __call__(self, *args) -> None:
        log_message = args[1] # last param
        logging.info("[DatasetLogPrior Log Message] "+log_message)
        logging.warning("args[0]: "+str(args[0]))
        self.function(args[0])


'''
@name Dataset (parent)
@description dataset class is the parent class
'''
class Dataset(Parser):

    file_location: str = "blank_file_location";
    location_type: str = "blank_file_type";

    def __init__(self, type):
        super().__init__()
        logging.info("Dataset constructor, type of ["+type+"]")

    '''
    Dataset get dataframe
    '''
    def get_dataframe(self):
        logging.info("Inside Dataset.get_dataframe()")
        return self.dataframe;



'''
@name CSV - child of Dataset
@description to handle csv files
'''
class CSV(Dataset):
    def __init__(self, parent_folder, folder, location_type):
        #call to Dataset class
        super().__init__("CSV") # becomes Dataset instance
        self.file_location = parent_folder+"/"+folder
        self.location_type = location_type

    '''
        - if the data is NOT in hadoop, read with pandas
        - if the data is in hadoop, read with sparkcsv
    '''
    def read(self) -> None:
        logging.info("Reading CSV")
        if self.location_type == "disk":
            self.read_from_disk(self, "Reading from disk for CSV")
        else:
            raise Exception("location_type "+self.location_type+" is not supported in CSV")

    '''
    @name get_size
    @description fetch the size of a pandas-based CSV, but still inherit
    '''
    def get_size(self) -> Tuple:
        logging.info("get_size()")
        df = super().get_dataframe() # fetch underlying dataframe from parent
        return df.data.shape

    '''
    @name read_from_disk
    @description read from disk, and set to objects dataframe
    '''
    @DatasetLogPrior
    def read_from_disk(self) -> None:
        logging.info("Trying: "+str(self.file_location))

        ## TODO: get columns from config
        df = pd.read_csv(self.file_location+"/bluecoat.log",
                         sep=r' ',
                         engine='python',
                         header=0,
                         error_bad_lines=False,
                         warn_bad_lines=False)

        # TODO: Parse class, will parse each row
        logging.warning("columns: "+str(df.columns)+":"+str(df.shape))

        '''
        foo = lambda x: pd.Series([ i for i inself.split_record(x, ' ') ])
        # apply the parser to each record
        rev = df["date"].head(10).apply(foo)
        '''
        logging.info( "Dataframe shape: ["+str(df.shape)+"]" )
        logging.error( df.describe() )
        self.dataframe = DataFrame( df )


'''
@name Dataset_Session
@description instance of using a dataset
'''
class DatasetSession():
    def __init__(self, type):
        logging.info("dataset session")
        self.dataset_type: str = type

    '''
    @name read_csv
    @description load the csv into the dataset sessions's dataset object
    '''
    def read_csv(self, data_folder: str, folder: str, location_type: str) -> None:
        logging.info("Dataset_Session: read_csv")
        self.dataset = CSV(data_folder, folder, location_type)
        self.dataset.read() # load into class dataset field, read from child class, not parent

    '''
    @name get_size
    @description get size of dataset_session's dataset object
    '''
    def get_size(self) -> Tuple:
        logging.warning("Getting Dataset size...")
        return self.dataset.get_size()

    '''
    @name get_dataset
    @description get size of dataset_session's dataset object
    '''
    def get_dataset(self) -> Dataset:
        return self.dataset

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

'''
@name dataset
@description purposed with dataset management, and interaction
'''

import logging
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Sequence, List
from enum import Enum
#from process import DataSourceFileType

'''
@name PriorSplitRecord
@description before split_record
'''

class PriorSplitRecord:
    def __init__(self, function):
        logging.info("PriorSplitRecord constructor")
        self.function = function

    def __call__(self, *args) -> List:
        logging.warning("PriorSplitRecord")
        logging.error("PriorSplitRecord args: "+str(args))
        logging.warning("PriorSplitRecord args len: "+str(len(args)))
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
    @name PriorSplitRecord
    @description, take in a record/row, and
    return an list of strings. @static because we only need one, and
    we don't need to keep a parser object in memory
    '''
    #@staticmethod
    @PriorSplitRecord
    def split_record(self, record: str, sep: str) -> List:
        logging.info("splitting record")
        split_result = record.split(sep)
        logging.warning("split record: "+str(split_result))
        return split_result


'''
@name CoreDataFrame
@description holds abstracted data frame. could hold dataframes from pandas, or pyspark
'''
class CoreDataFrame():
    def __init__(self, df):
        self.data = df

    def get_unique_id_set(self) -> None:
        logging.info("CoreDataFrame: get_unique_id_set")

'''
@name LogSourceType
#description enum of log source type
'''
class LogSourceType(Enum):
    DISK = "disk"
    HDFS = "hdfs"
    ES = "es"

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

    def __init__(self, type: str):
        super().__init__()
        logging.info("Dataset constructor, type of ["+type+"]")

    '''
    @description get dataframe set by Dataset
    '''
    def get_dataframe(self):
        logging.info("Inside Dataset.get_dataframe()")
        return self.dataframe;



'''
@name CSV - child of Dataset
@description to handle csv files
'''
class CSV(Dataset):
    def __init__(self, parent_folder: str, folder: str, location_type: str, delimiter: str):
        #call to Dataset class
        super().__init__("CSV Dataset") # becomes Dataset instance
        self.file_location = parent_folder+"/"+folder
        self.location_type = location_type
        self.delimiter = delimiter

    '''
        - if the data is NOT in hadoop, read with pandas
        - if the data is in hadoop, read with sparkcsv
    '''
    def read(self) -> None:
        logging.info("Reading CSV")
        if self.location_type == LogSourceType.DISK.value:
            self.read_from_disk(self, "Reading from disk for CSV")
        elif self.location_type == LogSourceType.HDFS.value:
            # read from hdfs
            pass
        else:
            raise Exception("location_type "+self.location_type+" is not supported in CSV")

    '''
    @name get_size
    @description fetch the size of a pandas-based CSV, but still inherit
    '''
    def get_size(self) -> Tuple:
        logging.info("get_size()")
        df = super().get_dataframe() # fetch underlying dataframe from parent
        return df.data.shape # will have to change the shape call to be general

    '''
    @name read_from_disk
    @description read from disk, and set to CSVs dataframe
    '''
    @DatasetLogPrior
    def read_from_disk(self) -> None:
        logging.info("Trying: "+str(self.file_location))

        ## TODO: get columns from config
        df = pd.read_csv(self.file_location+"/bluecoat.log",
                         sep=self.delimiter,
                         engine='python',
                         header=0,
                         error_bad_lines=False,
                         warn_bad_lines=False)

        # TODO: Parse class, will parse each row
        logging.info("columns: "+str(df.columns)+":"+str(df.shape))

        '''
        foo = lambda x: pd.Series([ i for i inself.split_record(x, ' ') ])
        # apply the parser to each record
        rev = df["date"].head(10).apply(foo)
        '''
        logging.info( "Dataframe shape: ["+str(df.shape)+"]" )
        logging.info( df.describe() )
        self.dataframe = CoreDataFrame( df )

    '''
    @name read_from_hdfs
    @description read from hdfs, and set to CSVs dataframe
    '''
    @DatasetLogPrior
    def read_from_hdfs(self) -> None:
        pass


'''
@name DatasetSession
@description instance of using a dataset
'''
class DatasetSession():
    def __init__(self, type: str):
        logging.info("dataset session")
        self.dataset_type: str = type

    '''
    @name read_csv
    @description load the csv into the dataset sessions's dataset object
    '''
    def read_csv(self, data_folder: str, folder: str, location_type: str, delimiter: str) -> None:
        logging.info("Dataset_Session: read_csv")
        self.dataset: CSV = CSV(data_folder, folder, location_type, delimiter)
        # load into class dataset field, read from parent class, not child
        self.dataset.read()

    '''
    @name get_size
    @description get size of dataset_session's dataset object
    '''
    def get_size(self) -> Tuple:
        return self.dataset.get_size()

    '''
    @name get_dataset
    @description get dataset_session's dataset object
    '''
    def get_dataset(self) -> Dataset:
        return self.dataset

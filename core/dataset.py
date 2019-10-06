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

class DataFrame():
    data = pd.DataFrame
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
        log_message = args[-1] # last param
        logging.info("[DatasetLogPrior Log Message] "+log_message)
        self.function(args[0])


'''
@name Dataset (parent)
@description dataset class is the parent class
'''
class Dataset():

    file_location: str = "blank_file_location";
    location_type: str = "blank_file_type";
    #dataframe: DataFrame = DataFrame;

    def __init__(self, type):
        logging.info("Dataset constructor, type of ["+type+"]")

    '''
    @name read_from_disk
    @description read from disk, and set to objects dataframe
    '''
    @DatasetLogPrior
    def read_from_disk(self) -> None:
        logging.info("Trying: "+str(self.file_location))

        #hard coded
        df = pd.read_csv(self.file_location+"/bluecoat.log",
                         sep=r'\\t',
                         engine='python')

        logging.info( "Dataframe shape: ["+str(df.shape)+"]" )
        logging.error( df.describe() )
        self.dataframe = DataFrame( df )

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
    def get_size(self) -> int:
        logging.info("get_size()")
        df = super().get_dataframe() # fetch underlying dataframe from parent
        shape = df.data.shape
        return shape[0]

'''
@name Dataset_Session
@description instance of using a dataset
'''
class Dataset_Session():
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
    def get_size(self) -> int:
        logging.warning("Getting Dataset size...")
        return self.dataset.get_size()

    '''
    @name get_dataset
    @description get size of dataset_session's dataset object
    '''
    def get_dataset(self) -> Dataset:
        return self.dataset

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
'''
@name process
@description Process engine is the default state of the system, whereby it will ingest
logs into the system

'''
import logging
from core.dataset import Dataset, DatasetSession, CoreDataFrame
from typing import Dict, Tuple, Sequence, List
from enum import Enum
from core.entity import GetAllEntities
from core.user import GetAllUsers, ExtractAllUsersCSV, UserSet, User
from pandas import DataFrame
from core.database import ReadJSONFileFS

DATASET_SCEME_URL: str = "./storage/scheme.json"

'''
@name DataSourceFileType
@description eum for data source file type
'''
class DataSourceFileType(Enum):
    CSV = "csv"
    FLAT = "flat"
    PARQUET = "parquet"
    JSON = "json"


'''
@name DataSource
@description class that holds representations for data sources
'''
class DataSource:
    def __init__(self):
        pass


class ProcessEngine():

    def __init__(self):
        logging.info("Process engine is initiated")

    '''
    @name execute
    @description run the process engine, which loads data into the system
    '''
    def execute(self) -> bool:
        logging.info("executing process engine")
        loaded_data_scheme: dict = ReadJSONFileFS(DATASET_SCEME_URL).data

        # for each data source_group
        for source_group in loaded_data_scheme["source_groups"]:

            data_folder = source_group["folder"]

            # load data from scheme above
            for log_obj in source_group["data"]:

                logging.info("Process: model Log_obj: "+str(log_obj["log_name"]))
                # TODO: load dataset index file holding dataset statuses

                #TODO: load "unprocessed" datasets, mostly by scheme set above in dataset_scheme

                # get the new dataframe
                log_file_dataset_session: DatasetSession = self.process_data(data_folder, log_obj)

                # TODO: condition on log_type, and location_type
                # TODO: with the CoreDataFrame from process data, perform user/entity analysis/extraction
                extracted_users: UserSet = ExtractAllUsersCSV.get(log_file_dataset_session, log_obj)
                test_user: str = str(list(extracted_users.users.keys())[:2])
                logging.info("ProcessEngine, execute, extracted_users, test user: "+test_user)


                # store the extracted users, or update the storage
                # extracted_users.set_of_users
                #TODO: mark log_obj as processed afterwards


        # get entities
        all_entities: dict = GetAllEntities().get()

        # get users
        all_users: dict = GetAllUsers().get()

        # after read the data, perform entity analysis using Entity types

        # adjust risk per entity

        return True

    '''
        @name process_data
        @param data_folder: str - the folder holding the files
        @param log_data_obj: dict - log config from the log set
        @return DatasetSession
        @description update the current data in the system for each log type.
        This means that we will load a new set of records into the system
    '''
    def process_data(self, data_folder: str, log_data_obj: dict) -> DatasetSession:

        logging.warning("Processing Data for : "+str(data_folder))

        log_name = log_data_obj["log_name"]
        log_type = log_data_obj["type"]
        delimiter = log_data_obj["delimiter"]
        location_type = log_data_obj["location_type"]
        folder = log_data_obj["folder"]
        id_feature = log_data_obj["id_feature"]

        dataset_session: DatasetSession = DatasetSession(log_type)

        #read dataset, if any new
        if log_type == DataSourceFileType.CSV.value:

            # invoke datasetsession to read the csv
            dataset_session.read_csv(data_folder, folder, location_type, delimiter) # load
            print( "isinstance(dataset_session.dataset, Dataset): "+str(isinstance(dataset_session.csv_dataset, Dataset)) )
            dataset_size: Tuple = dataset_session.get_csv_size()
            logging.info( "Dataset Session size: "+str(dataset_size) )

        elif log_type == DataSourceFileType.FLAT.value:
            pass
        elif log_type == DataSourceFileType.PARQUET.value:
            pass
        elif log_type == DataSourceFileType.JSON.value:
            pass

        return dataset_session

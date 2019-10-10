'''
Copyright 2019-Present The OpenUB Platform Authors
This file is part of the OpenUB Platform library.
The OpenUB Platform is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
The OpenUB Platform is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License
along with the OpenUB Platform. If not, see <http://www.gnu.org/licenses/>.
'''


'''
@name process
@description Process engine is the default state of the system, whereby it will ingest
logs into the system

'''
import logging
from dataset import Dataset, DatasetSession
from typing import Dict, Tuple, Sequence, List


dataset_scheme = {
    "mode": "test",
    "folder": "../test_datasets/toy_1",
    "data":
        [
            {
                "log_name": "proxy",
                "type": "csv",
                "location_type": "disk",
                "folder": "proxy"
            }
        ]
}

class ProcessEngine():

    def __init__(self):
        logging.info("Process engine is initiated")

    '''
    @name execute
    @description run the process engine
    '''
    def execute(self):
        logging.info("executing process engine")
        data_folder = dataset_scheme["folder"]
        # load data from scheme above, for test
        for log_obj in dataset_scheme["data"]:
            self.process_data(data_folder, log_obj)

    '''
        @name process_data
        @description update the current data in the system for each log type.
        This means that we will load a new set of records into the system
    '''
    def process_data(self, data_folder: str, log_data_obj: dict):

        logging.warning("Processing Data for : "+str(data_folder))

        log_name = log_data_obj["log_name"]
        log_type = log_data_obj["type"]
        location_type = log_data_obj["location_type"]
        folder = log_data_obj["folder"]

        dataset_session = DatasetSession(log_type)

        '''
         STEP1: check for new datasets
         from folder directory
        '''

        #read dataset, if any new
        if log_type == "csv":
            dataset_session.read_csv(data_folder, folder, location_type) # load
            print( "isinstance(dataset_session.dataset, Dataset): "+str(isinstance(dataset_session.dataset, Dataset)) )
            dataset_size: Tuple = dataset_session.get_size()
            logging.warning( "Dataset Session size: "+str(dataset_size) )

        # after read the data, perform entity analysis using Entity class

        # adjust risk per entity

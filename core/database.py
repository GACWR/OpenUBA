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
import logging
from enum import Enum
import json
import pandas as pd
import os.path
from typing import List

DB_CONFIG = {
    "type": "mongo"
}

class DBType(Enum):
    FS = 1
    HDFS = 2

'''
@name connector
@description this should enable the database, to be invoked using Query
'''
class Connector():
    def __init__(self, type):
        print("connector made")
        if type == "fs":
            self.type = FSConnectorType()
        elif type == "hdfs":
            self.type = HDFSConnector()
        else:
            raise Exception("Unsupported Connector type")

    def connect(self):
        self.type.attempt_to_connect()


'''
@name FSDBConnector
@description connect to flat files
'''
class FSConnector(Connector):
    def __init__(self):
        print("FS db type initiated")

    def attempt_to_connect(self):
        print("Connecting to FS")

'''
@name HDFSConnector
@description connect to HDFS
'''
class HDFSConnector(Connector):
    def __init__(self):
        print("HDFS db type initiated")

    def attempt_to_connect(self):
        print("Connecting to HDFS")




'''
@name DB
@description fundamental database parent class
'''
class DB():
    def __init__(self):
        print("db initiated")
        try:
            pass
        except Exception as e:
            logging.error(e)


'''
@name DBReadFile
@description read a raw file
'''
class DBReadFile(DB):
    def read_file(self, localtion: str) -> dict:
        logging.info("DBReadFile")
        return {}

'''
@name DBWriteFile
@description write a raw file
'''
class DBWriteFile(DB):
    def write_file(self, content: str, location: str, write_type: str = 'a') -> bool:
        logging.info("DBReadFile")
        try:
            with open(location, write_type) as file:
                file.write(content)
                return True
        except Exception as e:
            logging.error(str(e))
            return False

'''
@name WriteNewActorToDB
@description
'''
class WriteNewActorToDB(DBWriteFile):
    def set(self, actor_object: dict) -> bool:
        logging.info("write_actor")
        self.write_file(str(actor_object), "storage/TESTDBWRITENEWACTOR")
        return True

'''
@name ReadUserFromDB
@description
'''
class ReadActorFromDB(DBReadFile):
    def get(self, location: str) -> dict:
        logging.info("read_actor")
        return self.read_file(location)


'''
@name WriteListToDirectories
@description take a list, and create a directory for each element, given a parent directory
'''
class WriteListToDirectories():
    def __init__(self, list: List, parent_directory: str):
        logging.info("Write JSON file to directory")
        #TODO iterate over elements in list
        for element in list:
            #check if folder exists
            element_path: str = parent_directory+"/"+str(element)
            if os.path.exists(element_path):
            # exists, write x (nothing for now)
                pass
            else:
                # if doesnt exist
                # create directory
                os.mkdir(element_path)
            pass
            # stats
            os.stat(element_path)

'''
@name WriteJSONFileFS
@description write a json object to a file
'''
class WriteJSONFileFS():
    def __init__(self, data: dict, location: str):
        data_write: dict = data
        with open(location, 'w', encoding='utf-8') as f:
            json.dump(data_write, f, ensure_ascii=False, indent=4)

'''
@name ReadJSONFileFS
@description
'''
class ReadJSONFileFS():
    def __init__(self, location: str):
        # Read JSON file
        with open(location) as data_file:
            data_loaded = json.load(data_file)
            self.data: dict = data_loaded

'''
@name WritePKLFileFS
@description write a pickle file to a file
'''
class WritePKLFileFS():
    def __init__(self, data: dict, location: str):
        data_write: dict = data
        with open(location, 'w', encoding='utf-8') as f:
            json.dump(data_write, f, ensure_ascii=False, indent=4)


'''
@name ReadPKLFileFS
@description read a pickle file to a file
'''
class ReadPKLFileFS():
    def __init__(self, location: str):
        dataframe = pd.read_csv(location)

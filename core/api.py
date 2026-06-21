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
import logging
from core.entity import GetAllEntities
from core.user import GetAllUsers
from enum import Enum
from core.display import Display
from typing import Dict, Tuple, Sequence, List
import requests
import json


class APIType(Enum):
    GET_ALL_ENTITIES = "get_all_entities"
    GET_ALL_USERS = "get_all_users"
    GET_HOME_SUMMARY = "get_home_summary"
    GET_SYSTEM_LOG = "get_system_log"


'''
@name GetDisplayPrior
@description Grab the data for display
'''
class PriorGetDisplay:
    def __init__(self, function):
        logging.info("PriorGetDisplay OF TYPE -- __init__: "+str(function))

    def __call__(self, *args) -> str:
        display_type: str = args[0]
        logging.info("PriorGetDisplay OF TYPE -- __call__: "+args[0])

        # fetch the display data
        display = Display()
        logging.error("Display Type: "+str(display_type))
        logging.error("Display types 1: "+str(APIType.GET_ALL_ENTITIES.value))
        logging.error("Display types 2: "+str(APIType.GET_ALL_USERS.value))
        logging.error("Display types 3: "+str(APIType.GET_SYSTEM_LOG.value))

        if display_type == APIType.GET_ALL_ENTITIES.value:
            all_entities: dict = GetAllEntities().get()
            display.set(all_entities)
        elif display_type == APIType.GET_ALL_USERS.value:
            all_users: dict = GetAllUsers().get()
            display.set(all_users)
        elif display_type == APIType.GET_SYSTEM_LOG.value:
            system_display: dict = display.get_system_display()
            display.set(system_display)
        else:
            raise Exception("Unsupported API Display type")
        return str(display.data)


'''
@name API
@description Invoke API calls
'''
class API:
    @staticmethod
    @PriorGetDisplay
    def get_display_of_type(type: str) -> str:
        logging.info("API get_display type: "+str(type))
        return "test"

    @staticmethod
    def send_get_request(url: str, payload: dict, headers: dict):
        return requests.get(url,
                            data=json.dumps(payload),
                            headers=headers),

class LibraryAPI():
    def __init__(self):
        logging.info("Library API")

        # optional: point to a custom repo
        self.server: str = "http://openuba.gacwr.org"


    def install(self, model_name: str):
        url = self.server+"/ml/"
        payload = {
            "test": "test"
        }
        headers = {
            "content-type": "application/json"
        }
        return API.send_get_request(url, payload, headers)[0]

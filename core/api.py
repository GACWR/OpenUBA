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

import logging
from entity import GetAllEntities
from user import GetAllUsers
from enum import Enum
from display import Display
from typing import Dict, Tuple, Sequence, List


class APIType(Enum):
    GET_ALL_ENTITIES = "get_all_entities"
    GET_ALL_USERS = "get_all_users"
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

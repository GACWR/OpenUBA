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
import json
from core.database import DB, DBReadFile, DBType


'''
@name Display
@description a wrapper for a result to be displayed
'''
class Display():

    def __init__(self):
        logging.info("Display init")
        #self.data: dict = {"message": "display was never set beyond default"}

    def set(self, data: dict) -> None:
        self.data: dict = data

    def get_system_display(self) -> dict:

        logging.warning("get_system_display")

        # db object used for read
        db = DB()

        # todo: read from the system display

        data_to_display = dict()

        # tmp tests
        data_to_display["monitored_users"] = 23
        data_to_display["high_risk"] = 102
        data_to_display["total users"] = 23

        return data_to_display

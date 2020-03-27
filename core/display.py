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
import json
from database import DB, DBReadFile, DBType


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

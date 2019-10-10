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

import logging
import json

from database import DB



class Display():
    def __init__(self):
        logging.info("Display init")
        pass

    def get_system_display(self):

        logging.warning("get_system_display")
        db = DB()
        #db = client['pymongo_test']

        # some JSON:
        x =  '{ "name":"John", "age":30, "city":"New York"}'

        # parse x:
        y = json.loads(x)

        # the result is a Python dictionary:
        print(y["age"])

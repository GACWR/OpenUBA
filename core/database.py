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
@name database
@description To connect to any database, and submit queries
'''

import logging

'''

'''
class MongoDBConnectorType:
    def __init__(self):
        print("Mongo db type made")
    def attempt_to_connect(self):
        print("Connecting to mongo")

'''

'''
class HadoopConnectorType:
    def __init__(self):
        print("Mongo db type made")
    def attempt_to_connect(self):
        print("Connecting to mongo")

'''

'''
class SQLConnectorType:
    def __init__(self):
        print("Mongo db type made")
    def attempt_to_connect(self):
        print("Connecting to mongo")


'''

'''
class Connector():
    type = None;
    def __init__(self, type):
        print("connector made")
        if type == "mongodb":
            self.type = MongoDBConnectorType()
    def connect(self):
        self.type.attempt_to_connect()

'''

'''
class DB():
    def __init__(self):
        print("db made")
        db_connect = Connector()

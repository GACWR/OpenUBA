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
from pymongo import MongoClient


'''
@name DB
@description fundamental database parent class
'''
class DB():
    def __init__(self):
        print("db initiated")
        #db_connect = Connector()
        #client = MongoClient()
        try:
            client = MongoClient('localhost', 27017)
            #client = MongoClient('mongodb://localhost:27017')
            db = client['pymongo_test']
            posts = db.posts
            post_data = {
                'title': 'Python and MongoDB',
                'content': 'PyMongo is fun, you guys',
                'author': 'Scott'
            }
            result = posts.insert_one(post_data)
            print('One post: {0}'.format(result.inserted_id))
            scott_post = posts.find_one({'author': 'Scott'})
            print(scott_post)
        except Exception as e:
            logging.error(e)

'''
@name connector
@description this should enable the database, to be invoked using Query
'''
class Connector():
    def __init__(self, type):
        print("connector made")
        if type == "mongodb":
            self.type = MongoDBConnectorType()
        else:
            raise Exception("Unsupported Connector type")
    def connect(self):
        self.type.attempt_to_connect()


'''
@name MongoDBConnector
@description connect to mongo
'''
class MongoDBConnector(Connector):
    def __init__(self):
        print("Mongo db type made")
    def attempt_to_connect(self):
        print("Connecting to mongo")

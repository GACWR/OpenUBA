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
'''
@name entity
@description purposed for entity management
'''

import logging
from core.database import DBReadFile, DBWriteFile
from typing import Dict, Tuple, Sequence, List


'''
@name
@description
'''
class Entity():
    def __init__(self):
        logging.info("Entity is initiated")

'''
@name EntitySet
@description wrapper to hold a set of entities
'''
class EntitySet():
    def __init__(self):
        pass

'''
@name GetAllEntities
@description fetch all entities from the actual DB
'''
class GetAllEntities(DBReadFile):
    def get(self) -> dict:
        logging.info("read_user")
        #TODO: fetch all entities from storage, should not compute all entities (inefficient)
        #entities = self.read_file()
        return {"entity1": {}, "entity2": {}}

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
from hashlib import sha256
import logging

'''
@name Hash
@description
'''
class Hash():
    def __init__(self):
        pass

    def hash(self, bytes):
        return sha256(bytes)

'''
@name HashData
@description hash a str
'''
class HashData(Hash):
    def __init__(self, bytes):
        self.result: str = self.hash(bytes).hexdigest()

'''
@name HashFile
@description
'''
class HashFile(Hash):
    def __init__(self, filename):
        with open(filename,"rb") as f:
            bytes = f.read()
            readable_hash = self.hash(bytes).hexdigest();
        self.result: str = readable_hash

'''
@name HashLargeFile
@description
'''
class HashLargeFile(Hash):
    def __init__(self):
        sha256_hash = hashlib.sha256()
        with open(filename,"rb") as f:
            # update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096),b""):
                sha256_hash.update(byte_block)
            self.result = sha256_hash.hexdigest()

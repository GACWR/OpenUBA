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

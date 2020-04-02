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
import base64

'''
@name
@description
'''
class Base64():
    def encode(self, content: str):
        return base64.b64encode(content.encode())
    def decode(self, content: str):
        return base64.b64decode(content.encode())

'''
@name B64EncodeFile
@description
'''
class B64EncodeFile(Base64):
    def __init__(self, location: str):
        super().__init__()
        data = open(location, "r").read()
        self.result = self.encode(data)

'''
@name B64DecodeFile
@description
'''
class B64DecodeFile(Base64):
    def __init__(self, location: str):
        super().__init__()
        data = open(location, "r").read()
        self.result = self.decode(data)

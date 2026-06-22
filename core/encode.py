'''
Copyright (c) 2019–present Georgia Cyber Warfare Range
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
import base64

'''
@name
@description
'''
class Base64():
    def __init__(self, content: str = ""):
        self.content = content

    def encode(self, content: str = "") -> bytes:
        if content == "":
            return base64.b64encode( self.content.encode() )
        else:
            return base64.b64encode( content.encode() )

    def decode(self, content: str = "") -> bytes:
        if content == "":
            return base64.b64decode( self.content.encode() )
        else:
            return base64.b64decode( content.encode() )

'''
@name B64EncodeFile
@description
'''
class B64EncodeFile(Base64):
    def __init__(self, location: str):
        data = open(location, "r").read()
        self.result = self.encode(data)
        super().__init__()


'''
@name B64DecodeFile
@description
'''
class B64DecodeFile(Base64):
    def __init__(self, location: str):
        super().__init__()
        data = open(location, "r").read()
        self.result = self.decode(data)

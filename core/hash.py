import hashlib

'''
@name Hash
@description
'''
class Hash():
    def __init__(self):
        pass

    def hash(self, bytes):
        return hashlib.sha256(bytes)

'''
@name DataHasher
@description hash a str
'''
class DataHasher(Hash):
    def __init__(self, bytes):
        self.result = self.hash(bytes).hexdigest()

'''
@name DataHasher
@description
'''
class FileHasher(Hash):
    def __init__(self, filename):
        with open(filename,"rb") as f:
            bytes = f.read()
            readable_hash = self.hash(bytes).hexdigest();
            print(readable_hash)
        self.result = readable_hash

'''
@name LargeFileHasher
@description
'''
class LargeFileHasher(Hash):
    def __init__(self):
        sha256_hash = hashlib.sha256()
        with open(filename,"rb") as f:
            # update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096),b""):
                sha256_hash.update(byte_block)
            print(sha256_hash.hexdigest())

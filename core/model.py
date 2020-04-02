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
import threading
import time
import urllib.request
import sys
import os
import shutil
import io
from database import WriteJSONFileFS, ReadJSONFileFS
from user import GetAllUsers, UserSet, User
from encode import Base64, B64EncodeFile, B64DecodeFile
from utility import Timestamp

MODELS_LIBRARY_FILE_LOCATION = 'storage/models.json'
MODELS_SESSION_FILE_LOCATION = 'storage/model_sessions.json'

DEFAULT_MODEL_LIBRARY: dict = {
    "model_test": {
        "model_hash": "000000000000000",
        "model_name": "model_test",
        "enabled": True,
        "root": "ANJKD8aioh8wonsLAS9HWOI",
        "components": [
            {
                "filename": "__init__.py",
                "hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
            },
            {
                "filename": "model.py",
                "hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
            }
        ]
    }
}

TEST_MODEL_LIBRARY_RESPONSE: dict = {
    "models": {
        "model_test": {
            "components": [
                {
                    "filename": "__init__.py",
                    "hash": "b6367b2fd0968f2943909ab19a7618c44f77bfc2ec698a7a00c0b381c75de0d2",
                    "payload": b'ZnJvbSAubW9kZWxfdGVzdCBpbXBvcnQgZnVuY190cnk='
                },
                {
                    "filename": "model.py",
                    "hash": "214f5141510be21ca61f6ab957dc2eaa0e7e67d66c60309832f6d1c5a12710b7",
                    "payload": b'ZGVmIGZ1bmNfdHJ5KCk6CglwcmludCgibW9kZWxfdGVzdCB0ZXN0aW5nLi4uIikKCXJldHVybiAicmV0dXJuIGZyb20gbW9kZWxfVGVzdCI='
                }
            ]
        }
    }
}

class Model():
    def __init__(self, metadata: dict):
        self.data: dict = metadata
        pass

    def run(self):
        store_model
        pass

'''
@name ModelLibrary
@description manage model library
'''
class ModelLibrary():
    def __init__(self):
        self.server: str = "http://localhost::5000"


    def remove_model(self, model_id: int) -> bool:
        path = "model_library/model_test"
        try:
            #os.rmdir(path)
            shutil.rmtree(path)
            print("Model removed")
            return True
        except Exception as e:
            logging.error(e)
            return False

    '''
    @name install_model
    @description install selected model from server
    '''
    def install_model(self, model: Model):

        logging.error("installing model...")
        url = self.server+"/display/test/"

        # TODO: fetch model from API endpoint

        access_rights = 0o755
        path = "model_library/model_test/"
        try:
            os.mkdir(path, access_rights)
        except Exception as e:
            logging.error(e)

        model_payload: dict = TEST_MODEL_LIBRARY_RESPONSE["models"][model.data["model_name"]]

        logging.warning("install_model(), attempting to store")

        # TODO: run the test models
        self.store_model(model_payload)



    def is_installed(self, model: Model):
        return False

    def run_model(self, model: Model):


        sys.path.insert(1, 'model_library/'+str( model.data["model_name"] ))
        import model_test
        return model_test.execute()
        pass


    '''
    @name store_model
    @description
    '''
    def store_model(self, model: dict):

        logging.warning("storing model")
        # check if mode if installed

        #TODO verify, model_id is valid

        #TODO verify contents of model contents

        # insert at 1, 0 is the script path (or '' in REPL)

        # write model test code
        f = open('model_library/model_test/model_test.py', 'w')
        f.write("def execute():\n\tprint(\"model_test testing...\")\n\treturn \"return from model_Test\"")
        f.close()
        #
        f = open('model_library/model_test/__init__.py', 'w')
        f.write("from .model_test import execute")
        f.close()



'''
@name ModelDeployment
@description to alter deployed models set
'''
class ModelDeployment():
    def __init__(self, deployment_id: str):
        logging.info("Model Deployment made")
        self.did = deployment_id

'''
@Session
@description start model session. A model session can have several jobs
'''
class ModelSession():
    def __init__(self, metadata: dict, library: ModelLibrary):
        self.metadata: dict = metadata
        self.library: ModelLibrary = library

        #TODO: log model session has been initiated
        model_session_run_log_record: dict = {
            "session": metadata,
            "timestamp": Timestamp().readable
        }

        WriteJSONFileFS(model_session_run_log_record,
                        MODELS_SESSION_FILE_LOCATION)
    '''
    @name start_job
    @description start a model session job
    '''
    def start_job(self):
        logging.info("Model Session: starting job")
        time.sleep(2)

        model_instance: Model = Model(self.metadata)
        # model library load
        logging.info(str(model_instance.data))

        # check if model is installed
        model_id: str = model_instance.data["model_name"] # could be model hash

        # pass metadata so we can verify it is installed
        if not self.library.is_installed(model_instance):
            self.library.install_model(model_instance)
        else:
            pass

        self.library.run_model(model_instance)
        logging.info("Model Session: finishing job")



'''
@name ModelEngine
@description model engine runs all deployed models
'''
class ModelEngine():
    def __init__(self):
        self.library: ModelLibrary = ModelLibrary()

        # check for model metadata storage
        try:
            '''
            import os.path
            from os import path
            path.exists()
            '''
            json_reader = ReadJSONFileFS(MODELS_LIBRARY_FILE_LOCATION)
            self.models: dict = json_reader.data
            logging.info("Model Engine:"+str(self.models.keys()))
        except Exception as e:
            logging.error("ModelEngine: ReadJSONFileFS failed: "+str(e))
            self.models: dict = DEFAULT_MODEL_LIBRARY
            WriteJSONFileFS(self.models, MODELS_LIBRARY_FILE_LOCATION)
            pass

    def execute(self):
        #iterare over models
        for model in self.models.keys():
            logging.info("model engine execute model: "+str(model))
            model_metadata: dict = self.models[model]

            #if model is enable, load model, and run it
            if model_metadata["enabled"]:
                logging.info("Model enabled: "+str(model_metadata["model_name"]))
                model_session = ModelSession(model_metadata, self.library)

                # start model session job
                model_session.start_job()

            else:
                pass

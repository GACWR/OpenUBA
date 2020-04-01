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

'''
@name
@description for model sessions
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

MODELS_LIBRARY_FILE_LOCATION = 'storage/models.json'


'''
@name ModelLibrary
@description manage model library
'''
class ModelLibrary():
    def remove_model(self) -> bool:
        path = "model_library/model_test"
        try:
            #os.rmdir(path)
            shutil.rmtree(path)
            print("Model removed")
            return True
        except Exception as e:
            logging.error(e)
            return False

    def store_fetched_model(self):
        logging.info()

    def run_temp_model(self):
        ''' temporary files

        import tempfile

        # create a temporary directory
        with tempfile.TemporaryDirectory() as directory:
            print('The created temp dir is %s' % directory)

        '''
        pass


    def fetch_model(self):

        logging.error("fetching model...")
        url = "http://localhost:5000/display/test/"

        access_rights = 0o755
        path = "model_library/model_test/"
        try:
            os.mkdir(path, access_rights)
        except Exception as e:
            logging.error(e)

        '''
        @todo base 64 encode a model

        #sample_code = open('model.py', 'r')
        #sutf8 = sample_code.encode('UTF-8')
        '''

        logging.warning("codecs/io")

        with io.open("model.py",
                     'r',
                     encoding='utf8',
                     errors="ignore") as local_model:
            text = local_model.read()
            logging.warning(text)

        # write model test code
        f = open('model_library/model_test/model_test.py', 'w')
        f.write("def execute():\n\tprint(\"model_test testing...\")\n\treturn \"return from model_Test\"")
        f.close()

        f = open('model_library/model_test/__init__.py', 'w')
        f.write("from .model_test import execute")
        f.close()

        # insert at 1, 0 is the script path (or '' in REPL)
        sys.path.insert(1, 'model_library/'+str(model_id))

        import model_test
        return model_test.execute()

    def run_model(self):
        pass

    def load_model(self, model_id: str):

        #TODO verify, model_id is valid

        #TODO verify contents of model contents

        # insert at 1, 0 is the script path (or '' in REPL)
        sys.path.insert(1, 'model_library/'+str(model_id))

        import model_test
        return model_test.execute()


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
    def __init__(self):
        self.selected_model_name = "SK"

    '''
    start a model session
    '''
    def start_job(name):
        logging.info("Model Session %s: starting job")

        time.sleep(2)

        logging.info("Model Session %s: finishing job")



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
            self.models: dict = {
                "model_test": {
                    "model_name": "model_test",
                    "enabled": True
                }
            }
            WriteJSONFileFS(self.models, MODELS_LIBRARY_FILE_LOCATION)
            pass

    def execute(self):
        #iterare over models
        for model in self.models.keys():
            logging.info("model engine execute model: "+str(model))
            model_info: dict = self.models[model]

            #if model is enable, load model, and run it
            if model_info["enabled"]:
                logging.info("Model enabled: "+str(model_info["model_name"]))
                model_session = ModelSession()
            else:
                pass

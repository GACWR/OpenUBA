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
import os.path
from os import path
import shutil
import io
import json
from database import WriteJSONFileFS, ReadJSONFileFS
from user import GetAllUsers, UserSet, User
from encode import Base64, B64EncodeFile, B64DecodeFile
from hash import Hash, HashData, HashFile
from utility import Timestamp
from typing import List
from api import LibraryAPI

MODELS_LIBRARY_FILE_LOCATION: str = 'storage/models.json'
MODELS_SESSION_FILE_LOCATION: str = 'storage/model_sessions.json'


'''
@name Model
@description internal representation of a Model
'''
class Model():
    def __init__(self, metadata: dict):
        self.data: dict = metadata
        pass

    def run(self):
        store_model
        pass



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

    '''
    @name execute
    @description execute model job
    '''
    def execute(self):

        # TODO: reference model schedule, right now, this iterates over models sequentially
        #iterare over models in library
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



'''
@name ModelLibrary
@description manage model library
'''
class ModelLibrary():
    def __init__(self):
        self.api = LibraryAPI()

    '''
    @name
    @description
    '''
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

        # TODO: fetch model from API endpoint
        install_response = self.api.install(model.data["model_name"])

        logging.info("install_model() response: "+str(install_response.content.decode()))
        logging.info("install_model() raw: "+str(install_response.raw.headers))

        # Create folder
        access_rights = 0o755
        path = "model_library/"+str(model.data["model_name"])+"/"
        try:
            os.mkdir(path, access_rights)
        except Exception as e:
            logging.error(e)

        # parse model response object
        model_object: dict = json.loads(install_response.content.decode())["models"][model.data["model_name"]]

        logging.warning("install_model(), attempting to store: "+str(model.data["model_name"]))

        # TODO: store model
        self.store_model(model_object)


    '''
    @name is_installed
    @description
    '''
    def is_installed(self, model: Model):
        result: bool = True
        logging.info("is_installed: "+str( model.data["model_name"] ))
        if path.isdir("model_library/"+str(model.data["model_name"])+"/"):
            for component in model.data["components"]:
                if path.exists("model_library/"+str(model.data["model_name"])+"/"+str(component["filename"])):
                    logging.info("is_installed(): "+str( component["filename"] ))
                else:
                    logging.error("is_installed(): model component doesnt exist: "+str( component["filename"] ))
                    result = False
        else:
            logging.error("is_installed(), NO model directory: "+str( model.data["model_name"] ))
            result = False
        return result

    '''
    @name run_model
    @description
    '''
    def run_model(self, model: Model):
        logging.warning("run_model(), attempting to run: "+str(model.data["model_name"]))

        # import the model
        sys.path.insert(1, 'model_library/'+str( model.data["model_name"] ))
        import MODEL
        return MODEL.execute()


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
        # Iterate over components
        for component in model["components"]:
            # write binary
            f = open('model_library/'+model["model_name"] + '/' + component["filename"], 'wb')
            f.write( Base64( component["file_payload"] ).decode() )
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

        ## TODO: don't overwrite session log
        WriteJSONFileFS(model_session_run_log_record, MODELS_SESSION_FILE_LOCATION)

    '''
    @name start_job
    @description start a model session job
    '''
    def start_job(self):
        logging.info("Model Session: starting job")

        time.sleep(2) # TODO: remove after debug

        # create model instance
        model_instance: Model = Model(self.metadata)

        # model library load
        logging.info(str(model_instance.data))

        # check if model is installed
        model_id: str = model_instance.data["model_name"] # could be model hash

        # pass metadata so we can verify it is installed
        if not self.library.is_installed(model_instance):
            logging.info("Model Session, model is [NOT] installed: "+str(model_instance.data["model_name"]))
            if VerifyModel(model_instance).verify_model_encodings():
                self.library.install_model(model_instance)
                if VerifyModel(model_instance).verify_model_files():
                    model_result: dict = self.library.run_model(model_instance)
                    logging.info("Model Session: finishing job: "+str(len(model_result)))
                else:
                    # TODO: handle error
                    logging.error("Model Failed File Verification: "+str(model_instance.data))
                    # TODO: remove model
                    self.remove_model()
            else:
                # TODO: handle error
                logging.error("Model Failed Encoded Verification: "+str(model_instance.data))
                # TODO: remove model
                self.remove_model()
        else:
            logging.info("Model Session, model [IS] installed: "+str(model_instance.data["model_name"]))
            if VerifyModel(model_instance).verify_model_files():
                model_result: dict = self.library.run_model(model_instance)
                logging.info("Model Session: finishing job: "+str(len(model_result)))
            else:
                # TODO: handle error
                logging.error("Model Failed File Verification: "+str(model_instance.data))
                # TODO: remove model
                self.remove_model()

'''
@name VerifyModel
@description check integrity of model
'''
MAX_COMPONENTS: int = 2
class VerifyModel():
    def __init__(self, model: Model):
        self.model: Model = model

    '''
    @name verify_model_encodings
    @description
    '''
    def verify_model_encodings(self):
        hash_check: bool = True # start as correct, if error or invalid, change to false
        try:
            model_data: dict = self.model.data
            model_components: List = model_data["components"]
            if len(model_components) > MAX_COMPONENTS:
                logging.error("MODEL HAS TOO MANY COMPONENTS: "+str( model_data["model_name"] ))
            else:
                # iterate over components
                for component in model_data["components"]:
                    model_filename: str = str(component["filename"])

                    # cryptographically describe model
                    model_description: dict = ModelDescription(self.model, component).data()

                    if model_description["data_hash"].result == component["data_hash"]:
                        logging.info("verify_model_encodings, Model is VALID: " + str( model_data["model_name"] ) )
                        logging.info("Valid Component: " + str(component["filename"]) )

                        pass # check is valid
                    else:
                        hash_check = False # check is not valid
                        pass
                    logging.warning("hash_check: "+str( hash_check ))

        except Exception as e:
            logging.error("verify_model_encodings: "+str(e))
            hash_check = False

        return hash_check



    '''
    @name verify_model_files
    @description
    '''
    def verify_model_files(self):
        hash_check: bool = True # start as correct, if error or invalid, change to false
        #try:
        model_data: dict = self.model.data
        model_components: List = model_data["components"]
        if len(model_components) > MAX_COMPONENTS:
            logging.error("MODEL HAS TOO MANY COMPONENTS: "+str( model_data["model_name"] ))
        else:
            # iterate over components
            for component in model_data["components"]:
                model_filename: str = str(component["filename"])

                # cryptographically describe model
                model_description: dict = ModelDescription(self.model, component).files()

                if model_description["file_hash"].result == component["file_hash"]:
                    logging.info("verify_model_files, Model is VALID: " + str( model_data["model_name"] ) )
                    logging.info("Valid Component: " + str(component["filename"]) )
                    pass # check is valid
                else:
                    hash_check = False # check is not valid
                    pass

        # except Exception as e:
        #     logging.error("verify_model_files: "+str(e))
        #     hash_check = False

        return hash_check

'''
@name ModelDescription
@description
'''
class ModelDescription():
    def __init__(self, model: Model, component: dict):
        self.model = model
        self.component = component

    def data(self):

        # hash the base 64 representation of source
        data_hash = HashData(self.component["file_payload"].encode())
        logging.warning("Computed Component data hash: "+str(data_hash.result))

        description: dict = {
            "data_hash": data_hash
        }

        return description

    def files(self):
        # hash the file
        file_hash = HashFile("model_library/"+self.model.data["model_name"]+"/"+self.component["filename"])
        logging.warning("Computed Component file hash: "+str(file_hash.result))

        description: dict = {
            "file_hash": file_hash
        }

        return description
'''
@name DescribeModel
@description return encodings and hashes for a local model
'''
class DescribeModel():
    def __init__(self, model: str):
        logging.info("DescribeModel: "+str(model))
        self.model: str = model

    def describe(self):
        json_reader = ReadJSONFileFS(MODELS_LIBRARY_FILE_LOCATION)
        models: dict = json_reader.data
        model: Model = Model(models[self.model])
        description: dict = {}
        for component in model.data["components"]:
            description[component["filename"]+"_file_hash"] = HashFile("model_library/"+model.data["model_name"]+"/"+component["filename"]).result
            description[component["filename"]+"_file_b64"] = B64EncodeFile("model_library/"+model.data["model_name"]+"/"+component["filename"]).result
        return description

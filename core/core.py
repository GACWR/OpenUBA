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
@name core
@description manage the overall state of the platform
'''

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import threading
import time
from core.model import ModelLibrary, ProfileModel
from core.test import Test
from core.process import ProcessEngine
from core.api import API
from core.display import Display
from core.model import ModelEngine
import unittest
import trace, sys
import coloredlogs

coloredlogs.install()

'''
single server instance
@note dont use in prod, use a prodution ready WSGI server
'''
server = Flask(__name__)
CORS(server)

'''
@description endpoint to get varied display information
@note can be system_log, monitored_users, etc
'''
@server.route("/display/<string:display_type>/", methods=['GET'])
def display(display_type):
    logging.info("Getting display info with type: "+str(display_type))
    try:
        resp = jsonify(API.get_display_of_type(display_type))
        return resp
    except Exception as e:
        logging.error(str(e))
        return str("API display error")

'''
@description endpoint to disable a model
'''
@server.route("/disable_model/<string:model_name>/")
def delete_model(model_name):
    logging.warning("disabling model from api")
    return str(ModelLibrary().remove_model())

'''
@description endpoint to install a model
'''
@server.route("/install_model/<string:model_name>/")
def install_model(model_name):
    return ModelLibrary().install_model()

'''
@description retrieve system local model library
'''
@server.route("/models/")
def fetch_models():
    # return all local models
    return "TEST"


'''
@description retrieve a specific model from local model library
'''
@server.route("/model/<string:model_name>")
def fetch_specific_model(model_name):
    # return all local models
    return ''.join(["TEST",model_name])


'''
@name scheduler_run
@description function to start process engine
'''
def scheduler_run(name):
    logging.info("scheduler_run: "+str(name))

    #process engine, ingests new data
    process_engine_instance = ProcessEngine()
    process_engine_instance.execute()

    # model engine, performs each enabled model
    model_engine_instance = ModelEngine()
    model_engine_instance.execute()

    # risk engine

    # anomaly engine



'''
@name core
@description manage core system
'''
class Core:

    def __init__(self):
        pass
    '''
    @name initiate
    @description start core services
    '''
    def initiate(self):
        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format,
                            level=logging.INFO,
                            datefmt="%H:%M:%S")

        logging.info("Core: creating run_scheduler_job thread")

        # run scheduler
        self.run_scheduler_job()

        logging.warning("Core: created run_scheduler_job thread")

        # reset display storage
        self.run_display_information_job()

        #begin flask server, after initiation tasks
        # note: for v0.0.2, fastapi is the primary api server
        # flask is kept for legacy compatibility and scheduler
        # to run fastapi, use: uvicorn core.fastapi_app:app --host 0.0.0.0 --port 8000
        server.run(port=5001)  # run on different port to avoid conflict with fastapi

    '''
    @name run_scheduler_job
    @description start scheduler on a new thread.
    scheduler runs:
        - process engine
        - model engine
        - risk engine
        - anomaly engine
    '''
    def run_scheduler_job(self):
        x = threading.Thread(target=scheduler_run, args=("Test parameter to scheduler_run",))
        logging.info("core: before running thread")
        x.start()
        logging.info("core: wait for the thread to finish")

    '''
    @name run_display_information_job
    @description run display information job
    '''
    def run_display_information_job(self):
        print("Getting display information")
        self.display = Display()
        self.display.get_system_display()




if __name__ == "__main__":
    print("[Starting OpenUBA]")
    print(sys.argv)
    # TODO: refactor for more robust parameters
    if len(sys.argv) > 2:
        if sys.argv[1] == "profile_model":
            model_name: str = str(sys.argv[2])
            model_profile: dict = ProfileModel( model_name ).profile()
            for component in model_profile.keys():
                logging.info(str(component) + " : " + str(model_profile[component]))
        elif sys.argv[1] == "update_local_model":
            # model_name: str = str(sys.argv[2])

            # TODO: profile model,
            model_to_update: str = str(sys.argv[2])
            profile_for_model_to_update: dict = ProfileModel( model_to_update ).profile()

            # TODO: Update the local model library with the profile
            for component in profile_for_model_to_update.keys():
                logging.info(str(component) + " : " + str(profile_for_model_to_update[component]))
            pass
    else:
        Test.Run() # TODO: remove suite invocation
        core: Core = Core()
        core.initiate()

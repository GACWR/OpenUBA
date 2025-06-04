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
@name core
@description manage the overall state of the platform
'''

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import threading
import time
from model import ModelLibrary, ProfileModel
from test import Test
from process import ProcessEngine
from api import API
from display import Display
from model import ModelEngine
import unittest
import trace, sys
import coloredlogs
from database import ReadJSONFileFS
import os

STORAGE_DIR = 'storage'
RISK_RESULTS_FILE = os.path.join(STORAGE_DIR, 'risk_results.json')

# Create storage directory if it doesn't exist
os.makedirs(STORAGE_DIR, exist_ok=True)

# Initialize risk results file if it doesn't exist
if not os.path.exists(RISK_RESULTS_FILE):
    with open(RISK_RESULTS_FILE, 'w') as f:
        f.write('{}')

coloredlogs.install()

'''
single server instance
@note dont use in prod, use a prodution ready WSGI server
'''
server = Flask(__name__)

# Configure CORS to allow requests from React development server
CORS(server, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

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
        server.run(port=5001)

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

'''
@description endpoint to get user risk information
'''
@server.route("/api/users/risks", methods=['GET'])
def get_user_risks():
    try:
        risk_data = ReadJSONFileFS(RISK_RESULTS_FILE).data
        return jsonify(risk_data)
    except Exception as e:
        logging.error(f"Error reading risk data: {str(e)}")
        return jsonify({"error": "Failed to read risk data"})

'''
@description endpoint to get dashboard summary
'''
@server.route("/api/dashboard/summary", methods=['GET'])
def get_dashboard_summary():
    try:
        risk_data = ReadJSONFileFS(RISK_RESULTS_FILE).data
        high_risk_users = sum(1 for user, data in risk_data.items() if data.get('risk_score', 0) > 50)
        total_users = len(risk_data)
        
        return jsonify({
            "monitored_users": total_users,
            "high_risk": high_risk_users,
            "users_discovered": total_users,
            "users_imported": 0  # This would come from directory import
        })
    except Exception as e:
        logging.error(f"Error getting dashboard summary: {str(e)}")
        return jsonify({
            "monitored_users": 0,
            "high_risk": 0,
            "users_discovered": 0,
            "users_imported": 0
        })

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

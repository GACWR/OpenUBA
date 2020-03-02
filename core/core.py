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
from model import ModelLibrary
from test import Test
from process import ProcessEngine
from api import API
from display import Display
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
        return str("ssss")

'''
@description endpoint to disable a model
'''
@server.route("/disable_model/<string:model_name>/")
def delete_model(model_name):
    logging.warning("disabling model from api")
    return str(ModelLibrary.remove_model())

'''
@description endpoint to fetch a model
'''
@server.route("/fetch_model/<string:model_name>/")
def fetch_model(model_name):
    return ModelLibrary.fetch_model()


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
        server.run()

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
@name scheduler_run
@description function to start process engine
'''
def scheduler_run(name):
    logging.info("scheduler_run: "+str(name))

    #process engine
    process_engine_instance = ProcessEngine()
    process_engine_instance.execute()



    # model engine

    # risk engine

    # anomaly engine



if __name__ == "__main__":
    print("Core Start")
    Test.Run()
    core: Core = Core()
    core.initiate()

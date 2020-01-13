'''
Copyright 2019-Present The OpenUB Platform Authors
This file is part of the OpenUB Platform library.
The OpenUB Platform is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
The OpenUB Platform is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License
along with the OpenUB Platform. If not, see <http://www.gnu.org/licenses/>.
'''

'''
@name core
@description manage the overall state of the platform
'''

from flask import Flask
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
'''
server = Flask(__name__)

'''
@name scheduler_run
@description function to start process engine
'''
def scheduler_run(name):
    logging.info("scheduler_run: "+str(name))

    process_engine_instance = ProcessEngine()
    process_engine_instance.execute()


'''
@description endpoint to get varied display information
'''
@server.route("/display/<string:name>/")
def display(name):
    logging.info("Getting display info"+str(name))
    return API.get_display(name)

'''
@description endpoint to remove a model
'''
@server.route("/delete_model/<string:model_name>/")
def delete_model(model_name):
    logging.warning("deleting model.... from api")
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
        logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

        logging.info("Core: creating run_scheduler_job thread")
        ######run scheduler
        self.run_scheduler_job()

        logging.warning("Core: creating get_display_information thread")
        #reset display storage
        self.run_display_information_job()

        # get a model
        logging.info("Core: creating fetch_model_library thread")
        self.run_fetch_model_job()

        #begin flask server, after initiation tasks
        server.run()

    '''
    @name run_scheduler_job
    @description start scheduler on a new thread.
    scheduler runs:
        - process engine,
        - risk engine
        - model engine,
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
    @name run_fetch_model
    @description get model
    '''
    def run_fetch_model_job(self):
        print("Getting model")
        ModelLibrary.fetch_model()

if __name__ == "__main__":

    print("Core Start")
    ###############

    # Run all tests
    Test.Run()

    core: Core = Core()
    core.initiate()

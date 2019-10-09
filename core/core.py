'''
Copyright 2019-Present The OpenUEBA Platform Authors
This file is part of the OpenUEBA Platform library.
The OpenUEBA Platform is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
The OpenUEBA Platform is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License
along with the OpenUEBA Platform. If not, see <http://www.gnu.org/licenses/>.
'''

'''
@name core
@description manage the overall state of the platform
'''

from flask import Flask
import logging
import threading
import time
import model
from test import Test
from process import ProcessEngine
from api import API
from database import DB

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

    # model session
    #sess = model.Session()

    # start an instance of training using activate models
    #sess.start_job()

@server.route("/display/<string:name>/")
def display(name):
    logging.info("Getting display info"+str(name))
    return API.get_display(name)

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
        logging.info("core: before creating thread")
        self.run_scheduler_job()

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
        server.run()


if __name__ == "__main__":

    print("Core Start")
    ###############

    core: Core = Core()
    core.initiate()

    ###
    print("before DB")
    db = DB()
    print("after DB")

    # Run all tests
    Test.Run()

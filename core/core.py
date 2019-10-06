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
from process import ProcessEngine

import coloredlogs
coloredlogs.install()

server = Flask(__name__)

'''
function to start process engine
'''
def scheduler_run(name):
    logging.info("scheduler_run: "+str(name))

    process_engine_instance = ProcessEngine()
    process_engine_instance.execute()

    # model session
    #sess = model.Session()

    # start an instance of training using activate models
    #sess.start_job()

'''
@name get_dataset_info
@description fetch info on dataset
'''
@server.route("/get_dataset_info/<string:name>/")
def get_dataset_info(name):
    logging.info("Getting dataset info"+str(name))
    start_up("name test")
    return name


if __name__ == "__main__":

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("core: before creating thread")
    x = threading.Thread(target=scheduler_run, args=("Test parameter to scheduler_run",))

    logging.info("core: before running thread")

    x.start()
    logging.info("core: wait for the thread to finish")
    # x.join()
    logging.error("core: all done")

    server.run()

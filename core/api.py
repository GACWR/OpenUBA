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
from dataset import DatasetSession

'''
@name GetDisplayPrior
@description Grab the data for display
'''
class PriorGetDisplay:
    def __init__(self, function):
        logging.info("PriorGetDisplay -- __init__: "+str(function))

    def __call__(self, *args):
        logging.info("PriorGetDisplay -- __call__: "+args[0])

        # fetch the display data

        # insert into object
        display_object = dict()
        display_object["test"] = "1";
        return display_object


'''
@name API
@description Invoke API calls
'''
class API:
    @staticmethod
    @PriorGetDisplay
    def get_display(name) -> None:
        logging.info("API get_display"+str(name))
        #return name+"test"

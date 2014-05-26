# Copyright 2014 Zuercher Hochschule fuer Angewandte Wissenschaften
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

__author__ = 'andy'

import ConfigParser
import logging
from optparse import OptionParser
import time


DOING_PERFORMANCE_ANALYSIS = True

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

LOG = config_logger()

parser = OptionParser(usage="Usage: %prog options. See %prog -h for options.")

parser.add_option("-c", "--config",
                  action="store",
                  type="string",
                  dest="config_file_path",
                  help="Path to the service manager configuration file.")

(options, args) = parser.parse_args()

if not options.config_file_path:
    parser.error("Wrong number of arguments.")

LOG.info('Using config file: ' + options.config_file_path)

CONFIG = ConfigParser.ConfigParser()
CONFIG.read(options.config_file_path)

# helper function for to measure timedelta.
def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        LOG.debug("%r (%r, %r) %2.2f sec" % (method.__name__, args, kw, te-ts))
        return result, te-ts

    return timed

class conditional_decorator(object):
    def __init__(self, dec, condition):
        self.decorator = dec
        self.condition = condition

    def __call__(self, func):
        if not self.condition:
            return func
        else:
            return self.decorator(func)

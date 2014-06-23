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
import time

from optparse import OptionParser

DOING_PERFORMANCE_ANALYSIS = True


class DefaultConfigParser(ConfigParser.ConfigParser):

    def get(self, section, option, default='', raw=False, vars=None):
        try:
            value = ConfigParser.ConfigParser.get(self, section, option, raw, vars)
        except ConfigParser.NoOptionError:
            value = default
        return value


class conditional_decorator(object):
    # XXX: classes do CamelCase.
    def __init__(self, dec, condition):
        self.decorator = dec
        self.condition = condition

    def __call__(self, func):
        if not self.condition:
            return func
        else:
            return self.decorator(func)


def timeit(method):
    # helper function for to measure timedelta.
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        LOG.debug("%r (%r, %r) %2.2f sec" % (method.__name__, args, kw, te-ts))
        return result, te-ts

    return timed


def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger


def get_config_file():
    parser = OptionParser(usage="Usage: %prog options. See %prog -h for options.")
    parser.add_option("-c", "--config-file",
                      action="store",
                      type="string",
                      dest="config_file_path",
                      help="Path to the service manager configuration file.")
    parser.add_option("-p", "--perf-timings",
                      action="store_true",
                      dest="perf_timings",
                      default=False,
                      help="Enable performance timings within the SM.")
    (options, args) = parser.parse_args()

    if not options.config_file_path:
        parser.error("Wrong number of arguments.")

    return options

options = get_config_file()

DOING_PERFORMANCE_ANALYSIS = options.perf_timings
# XXX: above is redeclared from line #24

LOG = config_logger()
LOG.info('Using configuration file: ' + options.config_file_path)

CONFIG = DefaultConfigParser()
CONFIG.read(options.config_file_path)

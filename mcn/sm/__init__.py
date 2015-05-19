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
import os
import graypy

from optparse import OptionParser


class DefaultConfigParser(ConfigParser.ConfigParser):

    def get(self, section, option, default='', raw=False, vars=None):
        try:
            value = ConfigParser.ConfigParser.get(self, section, option, raw, vars)
        except ConfigParser.NoOptionError:
            value = default
        return value


def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: \t%(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    if CONFIG.get('general', 'log_file', '') != '':
        hdlr = logging.FileHandler(CONFIG.get('general', 'log_file', ''))
        formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

    if CONFIG.get('general', 'log_server', '') != '':
        from logging.handlers import SocketHandler, DEFAULT_TCP_LOGGING_PORT
        socketh = SocketHandler(CONFIG.get('general', 'log_server', ''), DEFAULT_TCP_LOGGING_PORT)
        logger.addHandler(socketh)

    if CONFIG.get('logging', 'graylog_api', '') != '' and CONFIG.get('logging', 'graylog_port', '') != '':

        gray_handler = graypy.GELFHandler(CONFIG.get('logging', 'graylog_api', ''), CONFIG.getint('logging', 'graylog_port'))
        logger.addHandler(gray_handler)

    return logger


def get_params():
    parser = OptionParser(usage="Usage: %prog options. See %prog -h for options.")
    parser.add_option("-c", "--config-file",
                      action="store",
                      type="string",
                      dest="config_file_path",
                      help="Path to the service manager configuration file.")
    (options, args) = parser.parse_args()

    if not options.config_file_path:
        parser.error("Wrong number of arguments.")

    return options

CONFIG = DefaultConfigParser()

if 'SM_CONFIG_PATH' in os.environ:
    config_file_path = os.getenv('SM_CONFIG_PATH')
    CONFIG.read(config_file_path)
else:
    options = get_params()
    config_file_path = options.config_file_path
    CONFIG.read(config_file_path)

LOG = config_logger()
LOG.info('Using configuration file: ' + config_file_path)

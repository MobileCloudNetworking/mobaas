# Copyright 2014-2015 Zuercher Hochschule fuer Angewandte Wissenschaften
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

import logging
import graypy

from sm.config import CONFIG

# XXX this will not work inside of OpenShift - needs to be modded
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

    if CONFIG.get('general', 'graylog_api', '') != '' and CONFIG.get('general', 'graylog_port', '') != '':
        gray_handler = graypy.GELFHandler(CONFIG.get('general', 'graylog_api', ''), CONFIG.getint('general', 'graylog_port'))
        logger.addHandler(gray_handler)
    
    return logger

LOG = config_logger()

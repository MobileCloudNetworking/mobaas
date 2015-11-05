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

import ConfigParser
import os
from optparse import OptionParser


class DefaultConfigParser(ConfigParser.ConfigParser):

    def get(self, section, option, default='', raw=False, vars=None):
        try:
            value = ConfigParser.ConfigParser.get(self, section, option, raw, vars)
        except ConfigParser.NoOptionError:
            value = default
        return value


def read():
    config = DefaultConfigParser()
    parser = OptionParser(usage="Usage: %prog options. See %prog -h for options.")
    parser.add_option("-c", "--config-file",
                      action="store",
                      type="string",
                      dest="config_file_path",
                      help="Path to the service manager configuration file.")
    (options, args) = parser.parse_args()

    config_file_path = ''
    # TODO add better default heuristics
    if 'SM_CONFIG_PATH' in os.environ:
        config_file_path = os.getenv('SM_CONFIG_PATH')
    elif options.config_file_path:
        config_file_path = options.config_file_path
    else:
        parser.error("SM: Wrong number of command line arguments.")

    config.read(config_file_path)

    return config, config_file_path


CONFIG, CONFIG_PATH = read()
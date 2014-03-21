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

from wsgiref.simple_server import make_server

from mcn.sm.backends import ServiceBackend
from mcn.sm import CONFIG


class Service():

    def __init__(self, app, srv_type):
        self.app = app
        self.service_backend = ServiceBackend()
        self.srv_type = srv_type

    def register_extension(self, mixin, backend):
        self.app.register_backend(mixin, backend)

    def run(self):
        #TODO require integration with AAA here - could SDK be used? Mefinks so :-)
        # register the Service & backend
        self.app.register_backend(self.srv_type, self.service_backend)

        httpd = make_server('', int(CONFIG.get('general', 'port')), self.app)
        httpd.serve_forever()

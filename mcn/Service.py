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
from occi.core_model import Kind
from occi.core_model import Resource
from ServiceBackend import ServiceBackend


class Service():

    def __init__(self, app, srv_types):
        self.app = app
        self.backend = ServiceBackend()
        self.srv_type = srv_types

        self.bundle_kind = Kind('http://mobile-cloud-networking.eu/sm#',
                  'bundle',
                  title='A service orchestrator bundle',
                  attributes={'mcn.bundle.location': 'required',
                              },
                  related=[Resource.kind],
                  actions=[])

    def register_extension(self, mixin, backend):
        self.app.register_backend(mixin, backend)

    def run(self):
        # register the bundle & backend
        self.app.register_backend(self.bundle_kind, self.backend)
        # register the Service & backend
        self.app.register_backend(self.srv_type, self.backend)

        #TODO pull this port from a config file
        httpd = make_server('', 8888, self.app)
        httpd.serve_forever()

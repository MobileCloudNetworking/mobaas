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

from occi.wsgi import Application
from occi.registry import NonePersistentRegistry

from mcn.sm.backends import ServiceBackend
from mcn.sm import CONFIG
from mcn.sm import LOG


class SMRegistry(NonePersistentRegistry):

    def __init__(self):
        super(SMRegistry, self).__init__()

    def add_resource(self, key, resource, extras):
        self.resources[resource.identifier] = resource

    def get_resource(self, key, extras):
        return self.resources[key]

class MCNApplication(Application):
    def __init__(self):
        super(MCNApplication, self).__init__(registry=SMRegistry())

    def register_backend(self, category, backend):
        return super(MCNApplication, self).register_backend(category, backend)

    def __call__(self, environ, response):
        auth = environ.get('HTTP_X_AUTH_TOKEN', '')
        # TODO validate the token against the AAA using the SDK

        if auth == '':
            LOG.error('No X-Auth-Token header supplied.')
            raise Exception('No X-Auth-Token header supplied.')

        tenant = environ.get('HTTP_X_TENANT_NAME', '')

        if tenant == '':
            LOG.error('No X-Tenant-Name header supplied.')
            raise Exception('No X-Tenant-Name header supplied.')

        return super(MCNApplication, self)._call_occi(environ, response, token=auth, tenant_name=tenant)


class Service():

    def __init__(self, app, srv_type):
        self.app = app
        self.service_backend = ServiceBackend()
        self.srv_type = srv_type

    def register_extension(self, mixin, backend):
        self.app.register_backend(mixin, backend)

    def run(self):
        # register the Service & backend
        self.app.register_backend(self.srv_type, self.service_backend)

        LOG.info('Service Manager running on interfaces, running on port: ' + CONFIG.get('general', 'port'))
        httpd = make_server('', int(CONFIG.get('general', 'port')), self.app)
        httpd.serve_forever()

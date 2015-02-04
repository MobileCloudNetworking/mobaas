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
import sys
import signal

from keystoneclient.v2_0 import client
from occi.exceptions import HTTPError
from occi.registry import NonePersistentRegistry
from occi.wsgi import Application

from mcn.sm.backends import ServiceBackend
from mcn.sm import CONFIG
from mcn.sm import LOG
from sdk.mcn import util


class SMRegistry(NonePersistentRegistry):

    def __init__(self):
        super(SMRegistry, self).__init__()

    def add_resource(self, key, resource, extras):
        self.resources[resource.identifier] = resource

    def get_resource(self, key, extras):
        # XXX: Omitting extras is potential dangerous and breaks multitenancy
        return self.resources[key]

    def get_resources(self, extras):
        # XXX: Omitting extras is potential dangerous and breaks multitenancy
        return self.resources.values()


class MCNApplication(Application):

    def __init__(self):
        super(MCNApplication, self).__init__(registry=SMRegistry())
        from occi.core_model import Link
        from occi.backend import KindBackend
        self.register_backend(Link.kind, KindBackend())

    def register_backend(self, category, backend):
        return super(MCNApplication, self).register_backend(category, backend)

    def __call__(self, environ, response):
        auth = environ.get('HTTP_X_AUTH_TOKEN', '')
        # TODO validate the token against the AAA using the SDK

        if auth == '':
            LOG.error('No X-Auth-Token header supplied.')
            raise HTTPError(401, 'No X-Auth-Token header supplied.')

        tenant = environ.get('HTTP_X_TENANT_NAME', '')

        if tenant == '':
            LOG.error('No X-Tenant-Name header supplied.')
            raise HTTPError(400, 'No X-Tenant-Name header supplied.')

        return self._call_occi(environ, response, token=auth, tenant_name=tenant, registry=self.registry)


class Service():

    def __init__(self, app, srv_type):
        self.app = app
        self.service_backend = ServiceBackend(app)
        self.srv_type = srv_type
        self.reg_srv = CONFIG.getboolean('service_manager_admin', 'register_service')
        if self.reg_srv:
            self.srv_ep = None
            self.ep = None
            self.token, self.tenant_name = self.get_service_credentials()
            self.design_uri = CONFIG.get('service_manager', 'design_uri', '')
            if self.design_uri == '':
                LOG.fatal('No design_uri parameter supplied in sm.cfg')
                raise Exception('No design_uri parameter supplied in sm.cfg')
            self.region = CONFIG.get('service_manager_admin', 'region', '')
            if self.region == '':
                LOG.info('No region parameter specified in sm.cfg, defaulting to RegionOne')
                self.region = 'RegionOne'
            self.service_endpoint = CONFIG.get('service_manager_admin', 'service_endpoint')
            if self.service_endpoint == '':
                LOG.fatal('No service_endpoint parameter supplied in sm.cfg')
                raise Exception()

    def get_service_credentials(self):

        token = CONFIG.get('service_manager_admin', 'service_token', '')
        if token == '':
            raise Exception('No service_token parameter supplied in sm.cfg')
        tenant_name = CONFIG.get('service_manager_admin', 'service_tenant_name', '')
        if tenant_name == '':
            raise Exception('No tenant_name parameter supplied in sm.cfg')

        return token, tenant_name

    def register_extension(self, mixin, backend):
        self.app.register_backend(mixin, backend)

    # TODO this functionality should be moved over to the SDK or put in the CC API
    def register_service(self):

        self.srv_ep = util.services.get_service_endpoint(identifier=self.srv_type.term, token=self.token,
                                                         endpoint=self.design_uri, tenant_name=self.tenant_name,
                                                         url_type='public')

        if self.srv_ep is None or self.srv_ep == '':
            LOG.debug('Registering the service with the keystone service...')

            keystone = client.Client(token=self.token, tenant_name=self.tenant_name, auth_url=self.design_uri)

            # taken from the kind definition
            self.srv_ep = keystone.services.create(self.srv_type.scheme+self.srv_type.term,
                                         self.srv_type.scheme+self.srv_type.term,
                                         self.srv_type.title)

            internal_url = admin_url = public_url = self.service_endpoint

            self.ep = keystone.endpoints.create(self.region, self.srv_ep.id, public_url, admin_url, internal_url)
            LOG.info('Service is now registered with keystone: ' +
                     'Region: ' + self.ep.region +
                     ' Public URL:' + self.ep.publicurl +
                     ' Service ID: ' + self.srv_ep.id +
                     ' Endpoint ID: ' + self.ep.id)
        else:
            LOG.info('Service is already registered with keystone. Service endpoint is: ' + self.srv_ep)

    def shutdown_handler(self, signum = None, frame = None):
        LOG.info('Service shutting down... ')
        if self.reg_srv:
            self.deregister_service()
        sys.exit(0)

    # TODO this functionality should be moved over to the SDK or put in the CC API
    def deregister_service(self):

        if self.srv_ep:
            LOG.debug('De-registering the service with the keystone service...')
            keystone = client.Client(token=self.token, tenant_name=self.tenant_name, auth_url=self.design_uri)
            keystone.services.delete(self.srv_ep.id)  # deletes endpoint too

    def run(self):
        self.app.register_backend(self.srv_type, self.service_backend)

        if self.reg_srv:
            self.register_service()

        # setup shutdown handler for deregistration of service
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, self.shutdown_handler)

        LOG.info('Service Manager running on interfaces, running on port: ' + CONFIG.get('general', 'port'))
        httpd = make_server('', int(CONFIG.get('general', 'port')), self.app)
        httpd.serve_forever()

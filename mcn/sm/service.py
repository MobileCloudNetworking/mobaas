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
            raise HTTPError(401, 'No X-Auth-Token header supplied.')

        tenant = environ.get('HTTP_X_TENANT_NAME', '')

        if tenant == '':
            LOG.error('No X-Tenant-Name header supplied.')
            raise HTTPError(400, 'No X-Tenant-Name header supplied.')

        return self._call_occi(environ, response, token=auth, tenant_name=tenant)


class Service():

    def __init__(self, app, srv_type):
        self.app = app
        self.service_backend = ServiceBackend(app)
        self.srv_type = srv_type

    def register_extension(self, mixin, backend):
        self.app.register_backend(mixin, backend)

    def run(self):
        self.app.register_backend(self.srv_type, self.service_backend)

        # TODO fix for if param not present in config file
        reg_srv = CONFIG.getboolean('service_manager_admin', 'register_service')
        if reg_srv:
            register_service(self.srv_type)

        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, shutdown_handler)

        LOG.info('Service Manager running on interfaces, running on port: ' + CONFIG.get('general', 'port'))
        httpd = make_server('', int(CONFIG.get('general', 'port')), self.app)
        httpd.serve_forever()


def shutdown_handler(signum = None, frame = None):
    LOG.info('Signal handler called with signal ' + str(signum))
    deregister_service()
    sys.exit(0)


# TODO this functionality should be moved over to the SDK or put in the CC API
def register_service(self, srv_type):
    ep = None
    design_uri = CONFIG.get('service_manager', 'design_uri', '')
    if design_uri == '':
        raise Exception('No design_uri parameter supplied in sm.cfg')
    token = CONFIG.get('service_manager_admin', 'service_token', '')
    if token == '':
        raise Exception('No service_token parameter supplied in sm.cfg')
    tenant_name = CONFIG.get('service_manager_admin', 'service_tenant_name', '')
    if tenant_name == '':
        raise Exception('No tenant_name parameter supplied in sm.cfg')

    srv_ep = util.services.get_service_endpoint(identifier=srv_type.term, token=token, endpoint=design_uri,
                                                tenant_name=tenant_name, url_type='public')
    if srv_ep is None or srv_ep == '':
        LOG.debug('Registering the service with the keystone service...')

        keystone = client.Client(token=token, tenant_name=tenant_name, auth_url=design_uri)

        # taken from the kind definition
        s = keystone.services.create(srv_type.scheme+srv_type.term, srv_type.scheme+srv_type.term, srv_type.title)

        region = CONFIG.get('service_manager_admin', 'region', '')
        if region == '':
            LOG.info('No region parameter specified in sm.cfg, defaulting to RegionOne')
            region = 'RegionOne'
        service_endpoint = CONFIG.get('service_manager_admin', 'service_endpoint')
        if service_endpoint == '':
            raise Exception('No service_endpoint parameter supplied in sm.cfg')

        internal_url = admin_url = public_url = service_endpoint

        ep = keystone.endpoints.create(region, s.id, public_url, admin_url, internal_url)
        LOG.debug('Service is now registered with keystone: ID: ' + ep.id + ' Region: ' + ep.region + ' Public URL:\
                    ' + ep.publicurl + ' Service ID: '+s.id)
    else:
        LOG.debug('Service is already registered with keystone. Service endpoint is: ' + srv_ep)

    return ep


def deregister_service():
    pass
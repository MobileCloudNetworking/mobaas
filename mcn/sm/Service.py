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

# XXX: Rename file to service.py

__author__ = 'andy'

from wsgiref.simple_server import make_server

from occi.wsgi import Application
from occi.registry import NonePersistentRegistry

from mcn.sm.backends import ServiceBackend
from mcn.sm import CONFIG
from mcn.sm import LOG
from sdk.mcn import util
from keystoneclient.v2_0 import client


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
            # XXX: better change to sending back 401 - don't throw exceptions around.

        tenant = environ.get('HTTP_X_TENANT_NAME', '')

        if tenant == '':
            LOG.error('No X-Tenant-Name header supplied.')
            raise Exception('No X-Tenant-Name header supplied.')

        # XXX: better: self._call_occi...
        return super(MCNApplication, self)._call_occi(environ, response, token=auth, tenant_name=tenant)


class Service():

    def __init__(self, app, srv_type):
        self.app = app
        self.service_backend = ServiceBackend()
        self.srv_type = srv_type

    def register_extension(self, mixin, backend):
        self.app.register_backend(mixin, backend)

    #TODO this functionality should be moved over to the SDK
    def register_service(self, srv_type):
        # XXX: following code should either a) solely use SDK or b) not use SDK ata ll and go to keystone directl.y
        # if not in keystone service regsitry, then register the service and its endpoints

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
            # TODO note in documentation that the admin URL should be accessible by the SM
            s = keystone.services.create(srv_type.scheme+srv_type.term, srv_type.scheme+srv_type.term, srv_type.title)

            region = CONFIG.get('service_manager_admin', 'region', '')
            if region == '':
                LOG.info('No region parameter specified in sm.cfg, defaulting to RegionOne')
                region = 'RegionOne'
            service_endpoint = CONFIG.get('service_manager_admin', 'service_endpoint')
            if service_endpoint == '':
                raise Exception('No service_endpoint parameter supplied in sm.cfg')

            #XXX it may be needed to specify internal, admin and pubilc URLs
            internalurl = adminurl = publicurl = service_endpoint

            ep = keystone.endpoints.create(region, s.id, publicurl, adminurl, internalurl)
            LOG.debug('Service is now registered with keystone: ID: ' + ep.id + ' Region: ' + ep.region + ' Public URL: ' + ep.publicurl + ' Service ID: '+s.id)
        else:
            LOG.debug('Service is already registered with keystone. Service endpoint is: ' + srv_ep)

        return

    def run(self):
        # register the Service & backend
        self.app.register_backend(self.srv_type, self.service_backend)

        #TODO fix for if param not present in config file
        reg_srv = CONFIG.getboolean('service_manager_admin', 'register_service')
        if reg_srv:
            self.register_service(self.srv_type)

        LOG.info('Service Manager running on interfaces, running on port: ' + CONFIG.get('general', 'port'))
        httpd = make_server('', int(CONFIG.get('general', 'port')), self.app)
        httpd.serve_forever()

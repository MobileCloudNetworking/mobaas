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

import json
import requests
import sys
import signal
from urlparse import urlparse

from keystoneclient.v2_0 import client
from occi.backend import KindBackend
from occi.core_model import Link, Kind, Resource
from occi.exceptions import HTTPError
from occi.registry import NonePersistentRegistry
from occi.wsgi import Application
from tornado import httpserver
from tornado import ioloop
from tornado import wsgi

from mcn.sm.backends import ServiceBackend
from mcn.sm.config import CONFIG
from mcn.sm.log import LOG
from sdk.mcn import util
from sdk.mcn.security import KeyStoneAuthService as token_checker


class SMRegistry(NonePersistentRegistry):

    def __init__(self):
        super(SMRegistry, self).__init__()

    def add_resource(self, key, resource, extras):
        self.resources[resource.identifier] = resource

    def get_resource(self, key, extras):
        # TODO: FIXME Omitting extras is potential dangerous and breaks tenant isolation
        return self.resources[key]

    def get_resources(self, extras):
        # TODO: FIXME Omitting extras is potential dangerous and breaks tenant isolation
        return self.resources.values()


class MCNApplication(Application):

    def __init__(self):
        super(MCNApplication, self).__init__(registry=SMRegistry())
        self.register_backend(Link.kind, KindBackend())

    def register_backend(self, category, backend):
        return super(MCNApplication, self).register_backend(category, backend)

    def __call__(self, environ, response):
        auth = environ.get('HTTP_X_AUTH_TOKEN', '')
        # TODO validate the token against the AAA using the SDK

        if auth == '':
            LOG.error('No X-Auth-Token header supplied.')
            raise HTTPError(400, 'No X-Auth-Token header supplied.')

        tenant = environ.get('HTTP_X_TENANT_NAME', '')

        if tenant == '':
            LOG.error('No X-Tenant-Name header supplied.')
            raise HTTPError(400, 'No X-Tenant-Name header supplied.')

        if not token_checker.verify(token=auth, tenant_name=tenant):
            raise HTTPError(401, 'Token is not valid. You likely need an updated token.')

        return self._call_occi(environ, response, token=auth, tenant_name=tenant, registry=self.registry)


class Service():

    def __init__(self, app, srv_type):
        self.app = app
        self.service_backend = ServiceBackend(app)
        LOG.info('Using configuration file: ' + 'TODO')  # TODO get this!
        self.reg_srv = CONFIG.getboolean('service_manager_admin', 'register_service')
        srv_type = self.create_service_type()
        self.srv_type = srv_type
        # NEW TODO token and tenant is now required in the config file
        self.token, self.tenant_name = self.get_service_credentials()
        self.design_uri = CONFIG.get('service_manager', 'design_uri', '')
        if self.design_uri == '':
                LOG.fatal('No design_uri parameter supplied in sm.cfg')
                raise Exception('No design_uri parameter supplied in sm.cfg')

        #NEW TODO STG MUST be supplied with a SM
        self.stg = None
        stg_path = CONFIG.get('service_manager', 'stg', '')
        with open(stg_path) as stg_content:
            self.stg = json.load(stg_content)
            stg_content.close()

        self.srv_ep = None
        self.ep = None
        if self.reg_srv:
            self.region = CONFIG.get('service_manager_admin', 'region', '')
            if self.region == '':
                LOG.info('No region parameter specified in sm.cfg, defaulting to an OpenStack default: RegionOne')
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

    def deregister_service(self):

        if self.srv_ep:
            LOG.debug('De-registering the service with the keystone service...')
            keystone = client.Client(token=self.token, tenant_name=self.tenant_name, auth_url=self.design_uri)
            keystone.services.delete(self.srv_ep.id)  # deletes endpoint too

    def run(self):
        self.app.register_backend(self.srv_type, self.service_backend)

        if self.reg_srv:
            self.register_service()

        # setup shutdown handler for de-registration of service
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, self.shutdown_handler)

        LOG.info('Service Manager running on interfaces, running on port: ' + CONFIG.get('general', 'port'))

        if self.DEBUG:
            from wsgiref.simple_server import make_server
            httpd = make_server('', int(CONFIG.get('general', 'port')), self.app)
            httpd.serve_forever()
        else:
            container = wsgi.WSGIContainer(self.app)
            http_server = httpserver.HTTPServer(container)
            http_server.listen(int(CONFIG.get('general', 'port')))
            ioloop.IOLoop.instance().start()

    def get_category(self, svc_kind):

        keystone = client.Client(token=self.token, tenant_name=self.tenant_name, auth_url=self.design_uri)

        try:
            svc = keystone.services.find(type=svc_kind.keys()[0])
            svc_ep = keystone.endpoints.find(service_id=svc.id)
        except Exception as e:
            LOG.error('Cannot find the service endpoint of: ' + svc_kind.__repr__())
            raise e

        u = urlparse(svc_ep.publicurl)

        # sort out the OCCI QI path
        if u.path == '/':
            svc_ep.publicurl += '-/'
        elif u.path == '':
            svc_ep.publicurl += '/-/'
        else:
            LOG.warn('Service endpoint URL does not look like it will work: ' + svc_ep.publicurl.__repr__())
            svc_ep.publicurl = u.scheme + '://' + u.netloc + '/-/'
            LOG.warn('Trying with the scheme and net location: ' + svc_ep.publicurl.__repr__())

        heads = {'X-Auth-Token': self.token, 'X-Tenant-Name': self.tenant_name, 'Accept': 'application/occi+json'}

        try:
            r = requests.get(svc_ep.publicurl, headers=heads)
            r.raise_for_status()
        except requests.HTTPError as err:
            print('HTTP Error: should do something more here!' + err.message)
            raise err

        registry = json.loads(r.content)

        category = None
        for cat in registry:
            if 'related' in cat:
                category = cat

        return Kind(scheme=category['scheme'], term=category['term'], related=category['related'], title=category['title'],
                    attributes=category['attributes'], location=category['location'])

    def get_dependencies(self):
        dependent_kinds = []
        for svc_type in self.stg['depends_on']:
            c = self.get_category(svc_type)
            if c:
                dependent_kinds.append(c)

        dependent_kinds.append(Resource.kind)
        return dependent_kinds

    def create_service_type(self):

        required_occi_kinds = self.get_dependencies()

        svc_scheme = self.stg['service_type'].split('#')[0] + '#'
        svc_term = self.stg['service_type'].split('#')[1]

        return Kind(
            scheme=svc_scheme,
            term=svc_term,
            related=required_occi_kinds,
            title=self.stg['service_description'],
            attributes=self.stg['service_attributes'],
            location='/' + svc_term + '/'
        )


class ServiceParameters():
    #TODO move this class into Service.py
    def __init__(self):
        self.service_params = {}
        service_params_file_path = CONFIG.get('service_manager', 'service_params', '')
        if len(service_params_file_path) > 0:
            try:
                with open(service_params_file_path) as svc_params_content:
                    self.service_params = json.load(svc_params_content)
                    svc_params_content.close()
            except ValueError as e:
                LOG.error("Invalid JSON sent as service config file")
            except IOError as e:
                LOG.error('Cannot find the specified parameters file: ' + service_params_file_path)
        else:
            LOG.warn("No service parameters file found in config file, setting internal params to empty.")

    def service_parameters(self, state='', content_type='text/occi'):
        # takes the internal parameters defined for the lifecycle phase...
        #       and combines them with the client supplied parameters
        if content_type == 'text/occi':
            params = []
            # get the state specific internal parameters
            try:
                params = self.service_params[state]
            except KeyError as err:
                LOG.warn('The requested states parameters are not available: "' + state + '"')

            # get the client supplied parameters if any
            try:
                for p in self.service_params['client_params']:
                    params.append(p)
            except KeyError as err:
                LOG.info('No client params')

            header = ''
            for param in params:
                if param['type'] == 'string':
                    value = '"' + param['value'] + '"'
                else:
                    value = str(param['value'])

                header = header + param['name'] + '=' + value + ', '

            return header[0:-2]
        else:
            LOG.error('Content type not supported: ' + content_type)

    def add_client_params(self, params={}):
        # adds user supplied parameters from the instantiation request of a service
        client_params = []

        for k, v in params.items():
            param_type = 'number'
            if (v.startswith('"') or v.startswith('\'')) and (v.endswith('"') or v.endswith('\'')):
                param_type = 'string'
                v = v[1:-1]
            param = {'name': k, 'value': v, 'type': param_type}

            client_params.append(param)

        self.service_params['client_params'] = client_params


if __name__ == '__main__':
    sp = ServiceParameters()
    cp = {
        'test': '1',
        'test.test': '"astring"'
    }
    sp.add_client_params(cp)

    p = sp.service_parameters('initialise')
    print p

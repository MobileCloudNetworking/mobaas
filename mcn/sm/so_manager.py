# Copyright 2014 Zuercher Hochschule fuer Angewandte Wissenschaften
# Copyright (c) 2013-2015, Intel Performance Learning Solutions Ltd, Intel Corporation.
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

from distutils import dir_util
from mako.template import Template
import os
import random
import requests
import shutil
import tempfile
from threading import Thread
from urlparse import urlparse

from mcn.sm import CONFIG
from mcn.sm import LOG


HTTP = 'http://'


class AsychExe(Thread):
    """
    Only purpose of this thread is to execute a list of tasks sequentially
    as a background "thread".
    """
    def __init__(self, tasks, registry=None):
        super(AsychExe, self).__init__()
        self.registry = registry
        self.tasks = tasks

    def run(self):
        super(AsychExe, self).run()
        LOG.debug('Starting AsychExe thread')

        for task in self.tasks:
            entity, extras = task.run()
            if self.registry:
                LOG.debug('Updating entity in registry')
                self.registry.add_resource(key=entity.identifier, resource=entity, extras=extras)


class Task():

    def __init__(self, entity, extras):
        self.entity = entity
        self.extras = extras

    def run(self):
        raise NotImplemented()


class InitSO(Task):

    def __init__(self, entity, extras):
        Task.__init__(self, entity, extras)
        self.nburl = CONFIG.get('cloud_controller', 'nb_api', '')
        if self.nburl[-1] == '/':
            self.nburl = self.nburl[0:-1]
        LOG.info('CloudController Northbound API: ' + self.nburl)

    def run(self):
        self.entity.attributes['mcn.service.state'] = 'initialising'
        LOG.debug('Ensuring SM SSH Key...')
        self.__ensure_ssh_key()

        # create an app for the new SO instance
        LOG.debug('Creating SO container...')
        if not self.entity.extras:
            self.entity.extras = {}
        self.entity.extras['repo_uri'] = self.__create_app()

        self.entity.attributes['mcn.service.state'] = 'initialised'

        return self.entity, self.extras

    def __create_app(self):
        # name must be A-Za-z0-9 and <=32 chars
        app_name = self.entity.kind.term[0:4] + 'srvinst' + ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        heads = {
            'Content-Type': 'text/occi',
            'Category': 'app; scheme="http://schemas.ogf.org/occi/platform#", '
            'python-2.7; scheme="http://schemas.openshift.com/template/app#", '
            'small; scheme="http://schemas.openshift.com/template/app#"',
            'X-OCCI-Attribute': 'occi.app.name=' + app_name
            }

        url = self.nburl + '/app/'
        LOG.debug('Requesting container to execute SO Bundle: ' + url)
        LOG.info('Sending headers: ' + heads.__repr__())
        r = _do_cc_request('POST', url, heads)

        loc = r.headers.get('Location', '')
        if loc == '':
            raise AttributeError("No OCCI Location attribute found in request")

        app_uri_path = urlparse(loc).path
        LOG.debug('SO container created: ' + app_uri_path)

        LOG.debug('Updating OCCI entity.identifier from: ' + self.entity.identifier + ' to: '
                  + app_uri_path.replace('/app/', self.entity.kind.location))
        self.entity.identifier = app_uri_path.replace('/app/', self.entity.kind.location)

        LOG.debug('Setting occi.core.id to: ' + app_uri_path.replace('/app/', ''))
        self.entity.attributes['occi.core.id'] = app_uri_path.replace('/app/', '')

        # get git uri. this is where our bundle is pushed to
        return self.__git_uri(app_uri_path)

    def __git_uri(self, app_uri_path):
        url = self.nburl + app_uri_path
        headers = {'Accept': 'text/occi'}
        LOG.debug('Requesting container\'s git URL ' + url)
        LOG.info('Sending headers: ' + headers.__repr__())
        r = _do_cc_request('GET', url, headers)

        attrs = r.headers.get('X-OCCI-Attribute', '')
        if attrs == '':
            raise AttributeError("No occi attributes found in request")

        repo_uri = ''
        for attr in attrs.split(', '):
            if attr.find('occi.app.repo') != -1:
                repo_uri = attr.split('=')[1][1:-1] # scrubs trailing wrapped quotes
                break
        if repo_uri == '':
            raise AttributeError("No occi.app.repo attribute found in request")

        LOG.debug('SO container repository: ' + repo_uri)

        return repo_uri

    def __ensure_ssh_key(self):
        url = self.nburl + '/public_key/'
        heads = {'Accept': 'text/occi'}
        resp = _do_cc_request('GET', url, heads)
        locs = resp.headers.get('x-occi-location', '')
        #Split on spaces, test if there is at least one key registered
        if len(locs.split()) < 1:
            LOG.debug('No SM SSH registered. Registering default SM SSH key.')
            occi_key_name, occi_key_content = self.__extract_public_key()

            create_key_headers = {'Content-Type': 'text/occi',
                                  'Category': 'public_key; scheme="http://schemas.ogf.org/occi/security/credentials#"',
                                  'X-OCCI-Attribute':'occi.key.name="' + occi_key_name + '", occi.key.content="' +
                                                     occi_key_content + '"'
            }
            _do_cc_request('POST', url, create_key_headers)
        else:
            LOG.debug('Valid SM SSH is registered with OpenShift.')

    def __extract_public_key(self):

        ssh_key_file = CONFIG.get('service_manager', 'ssh_key_location', '')
        if ssh_key_file == '':
            raise Exception('No ssh_key_location parameter supplied in sm.cfg')
        LOG.debug('Using SSH key file: ' + ssh_key_file)

        with open(ssh_key_file, 'r') as content_file:
            content = content_file.read()
            content = content.split()

            if content[0] == 'ssh-dsa':
                raise Exception("The supplied key is not a RSA ssh key. Location: " + ssh_key_file)

            key_content = content[1]
            key_name = 'servicemanager'

            if len(content) == 3:
                key_name = content[2]

            return key_name, key_content


class ActivateSO(Task):
    # TODO supply SM 'injected' params
    def __init__(self, entity, extras):
        Task.__init__(self, entity, extras)
        self.repo_uri = self.entity.extras['repo_uri']
        self.host = urlparse(self.repo_uri).netloc.split('@')[1]
        if os.system('which git') != 0:
            raise EnvironmentError('Git is not available.')

    def run(self):
        # get the code of the bundle and push it to the git facilities
        # offered by OpenShift
        self.entity.attributes['mcn.service.state'] = 'activating'
        LOG.debug('Deploying SO Bundle to: ' + self.repo_uri)
        self.__deploy_app()

        LOG.debug('Activating the SO...')
        self.__init_so()

        self.entity.attributes['mcn.service.state'] = 'activated'

        return self.entity, self.extras

    def __deploy_app(self):
        """
            Deploy the local SO bundle
            assumption here
            - a git repo is returned
            - the bundle is not managed by git
        """
        # create temp dir...and clone the remote repo provided by OpS
        dir = tempfile.mkdtemp()
        LOG.debug('Cloning git repository: ' + self.repo_uri + ' to: ' + dir)
        cmd = ' '.join(['git', 'clone', self.repo_uri, dir])
        os.system(cmd)

        # Get the SO bundle
        bundle_loc = CONFIG.get('service_manager', 'bundle_location', '')
        if bundle_loc == '':
            raise Exception('No bundle_location parameter supplied in sm.cfg')
        LOG.debug('Bundle to add to repo: ' + bundle_loc)
        dir_util.copy_tree(bundle_loc, dir)

        self.__add_openshift_files(bundle_loc, dir)

        # add & push to OpenShift
        os.system(' '.join(['cd', dir, '&&', 'git', 'add', '-A']))
        os.system(' '.join(['cd', dir, '&&', 'git', 'commit', '-m', '"deployment of SO for tenant ' + \
                            self.extras['tenant_name'] + '"', '-a']))
        LOG.debug('Pushing new code to remote repository...')
        os.system(' '.join(['cd', dir, '&&', 'git', 'push']))

        shutil.rmtree(dir)

    def __add_openshift_files(self, bundle_loc, dir):
        # put OpenShift stuff in place
        # build and pre_start_python comes from 'support' directory in bundle
        LOG.debug('Adding OpenShift support files from: ' + bundle_loc + '/support')

        # TODO generate these files automatically - no need for end-users to manage them
        # 1. Write build
        LOG.debug('Writing build to: ' + os.path.join(dir, '.openshift', 'action_hooks', 'build'))
        shutil.copyfile(bundle_loc+'/support/build', os.path.join(dir, '.openshift', 'action_hooks', 'build'))

        # 1. Write pre_start_python
        LOG.debug('Writing pre_start_python to: ' + os.path.join(dir, '.openshift', 'action_hooks', 'pre_start_python'))

        pre_start_template = Template(filename=bundle_loc+'/support/pre_start_python')
        design_uri = CONFIG.get('service_manager', 'design_uri', '')
        content = pre_start_template.render(design_uri=design_uri)
        LOG.debug('Writing pre_start_python content as: ' + content)
        pre_start_file = open(os.path.join(dir, '.openshift', 'action_hooks', 'pre_start_python'), "w")
        pre_start_file.write(content)
        pre_start_file.close()

        os.system(' '.join(['chmod', '+x', os.path.join(dir, '.openshift', 'action_hooks', '*')]))

    # example request to the SO
    # curl -v -X PUT http://localhost:8051/orchestrator/default \
    #   -H 'Content-Type: text/occi' \
    #   -H 'Category: orchestrator; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"' \
    #   -H 'X-Auth-Token: '$KID \
    #   -H 'X-Tenant-Name: '$TENANT
    def __init_so(self):
        url = HTTP + self.host + '/orchestrator/default'
        heads = {
            'Category': 'orchestrator; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"',
            'Content-Type': 'text/occi',
            'X-Auth-Token': self.extras['token'],
            'X-Tenant-Name': self.extras['tenant_name'],
        }
        LOG.debug('Initialising SO with: ' + url)
        LOG.info('Sending headers: ' + heads.__repr__())

        try:
            r = requests.put(url, headers=heads)
            r.raise_for_status()
        except requests.HTTPError as err:
            LOG.error('HTTP Error: should do something more here!' + err.message)
            raise err


class DeploySO(Task):
    # TODO supply SM 'injected' params
    def __init__(self, entity, extras):
        Task.__init__(self, entity, extras)
        self.repo_uri = self.entity.extras['repo_uri']
        self.host = urlparse(self.repo_uri).netloc.split('@')[1]

    # example request to the SO
    # curl -v -X POST http://localhost:8051/orchestrator/default?action=deploy \
    #   -H 'Content-Type: text/occi' \
    #   -H 'Category: deploy; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"' \
    #   -H 'X-Auth-Token: '$KID \
    #   -H 'X-Tenant-Name: '$TENANT
    def run(self):
        # Deployment is done without any control by the client...
        # otherwise we won't be able to hand back a working service!
        self.entity.attributes['mcn.service.state'] = 'deploying'
        LOG.debug('Deploying the SO bundle...')
        url = HTTP + self.host + '/orchestrator/default'
        params = {'action': 'deploy'}
        heads = {
            'Category': 'deploy; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"',
            'Content-Type': 'text/occi',
            'X-Auth-Token': self.extras['token'],
            'X-Tenant-Name': self.extras['tenant_name']}
        LOG.debug('Deploying SO with: ' + url)
        LOG.info('Sending headers: ' + heads.__repr__())

        try:
            r = requests.post(url, headers=heads, params=params)
            r.raise_for_status()
        except requests.HTTPError as err:
            LOG.error('HTTP Error: should do something more here!' + err.message)
            raise err

        self.entity.attributes['mcn.service.state'] = 'deployed'
        LOG.debug('SO Deployed ')
        return self.entity, self.extras


class ProvisionSO(Task):
    # TODO supply SM 'injected' params
    def __init__(self, entity, extras):
        Task.__init__(self, entity, extras)
        self.repo_uri = self.entity.extras['repo_uri']
        self.host = urlparse(self.repo_uri).netloc.split('@')[1]

    def run(self):
        self.entity.attributes['mcn.service.state'] = 'provisioning'
        url = HTTP + self.host + '/orchestrator/default'
        params = {'action': 'provision'}
        heads = {
            'Category': 'provision; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"',
            'Content-Type': 'text/occi',
            'X-Auth-Token': self.extras['token'],
            'X-Tenant-Name': self.extras['tenant_name']}
        LOG.debug('Provisioning SO with: ' + url)
        LOG.info('Sending headers: ' + heads.__repr__())

        try:
            r = requests.post(url, headers=heads, params=params)
            r.raise_for_status()
        except requests.HTTPError as err:
            LOG.error('HTTP Error: should do something more here!' + err.message)
            raise err

        self.entity.attributes['mcn.service.state'] = 'provisioned'
        return self.entity, self.extras


class RetrieveSO(Task):

    def __init__(self, entity, extras):
        Task.__init__(self, entity, extras)
        repo_uri = self.entity.extras['repo_uri']
        self.host = urlparse(repo_uri).netloc.split('@')[1]

    def run(self):
        # example request to the SO
        # curl -v -X GET http://localhost:8051/orchestrator/default \
        #   -H 'X-Auth-Token: '$KID \
        #   -H 'X-Tenant-Name: '$TENANT

        if self.entity.attributes['mcn.service.state'] in ['activated', 'deployed', 'provisioned']:
            heads = {
                'Content-Type': 'text/occi',
                'Accept': 'text/occi',
                'X-Auth-Token': self.extras['token'],
                'X-Tenant-Name': self.extras['tenant_name']}
            LOG.info('Getting state of service orchestrator with: ' + self.host + '/orchestrator/default')
            LOG.info('Sending headers: ' + heads.__repr__())

            try:
                r = requests.get(HTTP + self.host + '/orchestrator/default', headers=heads)
                r.raise_for_status()
            except requests.HTTPError as err:
                LOG.error('HTTP Error: should do something more here!' + err.message)
                raise err

            attrs = r.headers['x-occi-attribute'].split(', ')
            for attr in attrs:
                kv = attr.split('=')
                if kv[0] != 'occi.core.id':
                    if kv[1].startswith('"') and kv[1].endswith('"'):
                        kv[1] = kv[1][1:-1]  # scrub off quotes
                    self.entity.attributes[kv[0]] = kv[1]
                    LOG.debug('OCCI Attribute: ' + kv[0] + ' --> ' + kv[1])
        else:
            LOG.debug('Cannot GET entity as it is not in the activated, deployed or provisioned state')

        return self.entity, self.extras


class DestroySO(Task):
    def __init__(self, entity, extras):
        Task.__init__(self, entity, extras)
        self.nburl = CONFIG.get('cloud_controller', 'nb_api', '')
        repo_uri = self.entity.extras['repo_uri']
        self.host = urlparse(repo_uri).netloc.split('@')[1]

    def run(self):
        # 1. dispose the active SO, essentially kills the STG/ITG
        # 2. dispose the resources used to run the SO
        # example request to the SO
        # curl -v -X DELETE http://localhost:8051/orchestrator/default \
        #   -H 'X-Auth-Token: '$KID \
        #   -H 'X-Tenant-Name: '$TENANT
        url = HTTP + self.host + '/orchestrator/default'
        heads = {'X-Auth-Token': self.extras['token'],
                 'X-Tenant-Name': self.extras['tenant_name']}
        LOG.info('Disposing service orchestrator with: ' + url)
        LOG.info('Sending headers: ' + heads.__repr__())

        try:
            r = requests.delete(url, headers=heads)
            r.raise_for_status()  # TODO if error report verbosely and perform recovery
        except requests.HTTPError as err:
            LOG.error('HTTP Error: should do something more here!' + err.message)
            raise err

        url = self.nburl + self.entity.identifier.replace('/' + self.entity.kind.term + '/', '/app/')
        heads = {'Content-Type': 'text/occi',
                 'X-Auth-Token': self.extras['token'],
                 'X-Tenant-Name': self.extras['tenant_name']}
        LOG.info('Disposing service orchestrator container via CC... ' + url)
        LOG.info('Sending headers: ' + heads.__repr__())
        _do_cc_request('DELETE', url, heads)

        return self.entity, self.extras


def _do_cc_request(verb, url, heads):
    """
    Do a simple HTTP request.

    :param verb: One of POST, DELETE, GET
    :param url: The URL to use.
    :param heads: The headers.
    :return: the response headers.
    """
    user = CONFIG.get('cloud_controller', 'user')
    pwd = CONFIG.get('cloud_controller', 'pwd')
    if verb in ['POST', 'DELETE', 'GET']:
        try:
            if verb == 'POST':
                r = requests.post(url, headers=heads, auth=(user, pwd))
            elif verb == 'DELETE':
                r = requests.delete(url, headers=heads, auth=(user, pwd))
            elif verb == 'GET':
                r = requests.get(url, headers=heads, auth=(user, pwd))
            r.raise_for_status() # TODO if error report verbosely and perform recovery
            return r
        except requests.HTTPError as err:
            LOG.error('HTTP Error: should do something more here!' + err.message)
            raise err
    else:
        LOG.error('Supplied verb is unknown: ' + verb)
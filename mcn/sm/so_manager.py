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
import multiprocessing
import os
import random
import requests
import shutil
import tempfile
from urlparse import urlparse

from mcn.sm import CONFIG
from mcn.sm import LOG
from mcn.sm import timeit, conditional_decorator, DOING_PERFORMANCE_ANALYSIS


HTTP = 'http://'


class CreateSOProcess(multiprocessing.Process):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(CreateSOProcess, self).__init__(group, target, name, args, kwargs)
        self.entity = args[0]
        self.extras = args[1]
        self.nburl = CONFIG.get('cloud_controller', 'nb_api', '')
        if self.nburl[-1] == '/':
            self.nburl = self.nburl[0:-1]
        LOG.info('CloudController Northbound API: ' + self.nburl)

    def run(self):
        super(CreateSOProcess, self).run()
        self.__create_so()

    @conditional_decorator(timeit, DOING_PERFORMANCE_ANALYSIS)
    def __create_so(self):
        LOG.debug('Ensuring SM SSH Key...')
        self.__ensure_ssh_key()

        # create an app for the new SO instance
        LOG.debug('Creating SO container...')
        repo_uri = self.__create_app()

        #send back the repo URI and new resource id
        q = self.extras['ret_q']
        ret_val={'repo_uri': repo_uri, 'identifier': self.entity.identifier}
        q.put(ret_val)

    def __create_app(self):

        # name must be A-Za-z0-9 and <=32 chars
        app_name = self.entity.kind.term[0:4] + 'srvinst' + ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        create_app_headers = {
            'Content-Type': 'text/occi',
            'Category': 'app; scheme="http://schemas.ogf.org/occi/platform#", '
            'python-2.7; scheme="http://schemas.openshift.com/template/app#", '
            'small; scheme="http://schemas.openshift.com/template/app#"',
            'X-OCCI-Attribute': 'occi.app.name=' + app_name
            }

        url = self.nburl + '/app/'
        LOG.debug('Requesting container to execute SO Bundle: ' + url)
        r = _do_cc_request('POST', url, create_app_headers)

        loc = r.headers.get('Location', '')
        if loc == '':
            raise AttributeError("No OCCI Location attribute found in request")

        app_uri_path = urlparse(loc).path
        LOG.debug('SO container created: ' + app_uri_path)

        #TODO need to fix this in the OCCI web app context!
        LOG.debug('Updating OCCI entity.identifier from: ' + self.entity.identifier + ' to: '
                  + app_uri_path.replace('/app/', self.entity.kind.location))
        self.entity.identifier = app_uri_path.replace('/app/', self.entity.kind.location)

        LOG.debug('Setting occi.core.id to: ' + app_uri_path.replace('/app/', ''))
        self.entity.attributes['occi.core.id'] = app_uri_path.replace('/app/', '')

        # get git uri. this is where our bundle is pushed to
        url = self.nburl + app_uri_path
        headers = {'Accept': 'text/occi'}
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
                'X-OCCI-Attribute':'occi.key.name="' + occi_key_name + '", occi.key.content="' + occi_key_content + '"'
            }
            resp = _do_cc_request('POST', url, create_key_headers)
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


class DeploySOProcess(multiprocessing.Process):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(DeploySOProcess, self).__init__(group, target, name, args, kwargs)
        self.entity = args[0]
        self.extras = args[1]
        self.repo_uri = self.entity.extras['repo_uri']

        if os.system('which git') != 0:
            raise EnvironmentError('Git is not available.')

    def run(self):
        super(DeploySOProcess, self).run()
        self.deploy_so()

    def deploy_so(self):
        # get the code of the bundle and push it to the git facilities
        # offered by OpenShift
        LOG.debug('Deploying SO Bundle to: ' + self.repo_uri)
        self.__deploy_app(self.repo_uri)

        host = urlparse(self.repo_uri).netloc.split('@')[1]

        LOG.debug('Creating the SO...')
        self.__init_so(host)

        # Deployment is done without any control by the client...
        # otherwise we won't be able to hand back a working service!
        LOG.debug('Deploying the SO bundle...')
        self.__deploy_so(host)

    # example request to the SO
    # curl -v -X PUT http://localhost:8051/orchestrator/default \
    #   -H 'Content-Type: text/occi' \
    #   -H 'Category: orchestrator; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"' \
    #   -H 'X-Auth-Token: '$KID \
    #   -H 'X-Tenant-Name: '$TENANT
    def __init_so(self, host):
        url = HTTP + host + '/orchestrator/default'
        heads = {
            'Category': 'orchestrator; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"',
            'Content-Type': 'text/occi',
            'X-Auth-Token': self.extras['token'],
            'X-Tenant-Name': self.extras['tenant_name'],
        }

        LOG.debug('Initialising SO with: ' + url)
        # TODO: send `entity`'s attributes along with the call to deploy
        r = requests.put(url, headers=heads)
        r.raise_for_status()

    # example request to the SO
    # curl -v -X POST http://localhost:8051/orchestrator/default?action=deploy \
    #   -H 'Content-Type: text/occi' \
    #   -H 'Category: deploy; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"' \
    #   -H 'X-Auth-Token: '$KID \
    #   -H 'X-Tenant-Name: '$TENANT
    def __deploy_so(self, host):
        url = HTTP + host + '/orchestrator/default'
        params = {'action': 'deploy'}
        heads = {
            'Category': 'deploy; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"',
            'Content-Type': 'text/occi',
            'X-Auth-Token': self.extras['token'],
            'X-Tenant-Name': self.extras['tenant_name']}
        LOG.debug('Deploying SO with: ' + url)
        r = requests.post(url, headers=heads, params=params)
        r.raise_for_status()

        # Store the stack id. This should not be shown to the EEU.
        if r.content == 'Please initialize SO with token and tenant first.':
            self.entity.attributes['mcn.service.state'] = 'failed'
            raise Exception('Error deploying the SO')
        else:
            LOG.debug('SO Deployed ')

    def __deploy_app(self, repo):
        """
            Deploy the local SO bundle
            assumption here
            - a git repo is returned
            - the bundle is not managed by git
        """

        # create temp dir...and clone the remote repo provided by OpS
        dir = tempfile.mkdtemp()
        LOG.debug('Cloning git repository: ' + repo + ' to: ' + dir)
        cmd = ' '.join(['git', 'clone', repo, dir])
        os.system(cmd)

        # Get the SO bundle
        bundle_loc = CONFIG.get('service_manager', 'bundle_location', '')
        if bundle_loc == '':
            raise Exception('No bundle_location parameter supplied in sm.cfg')
        LOG.debug('Bundle to add to repo: ' + bundle_loc)
        dir_util.copy_tree(bundle_loc, dir)

        # put OpenShift stuff in place
        # build and pre_start_python comes from 'support' directory in bundle
        # XXX could be improved - e.g. could use from mako.template import Template? - use this to inject the design_uri
        LOG.debug('Adding OpenShift support files from: ' + bundle_loc + '/support')

        shutil.copyfile(bundle_loc+'/support/build', os.path.join(dir, '.openshift', 'action_hooks', 'build'))
        shutil.copyfile(bundle_loc+'/support/pre_start_python', os.path.join(dir, '.openshift', 'action_hooks', 'pre_start_python'))

        os.system(' '.join(['chmod', '+x', os.path.join(dir, '.openshift', 'action_hooks', '*')]))

        # add & push to OpenShift
        os.system(' '.join(['cd', dir, '&&', 'git', 'add', '-A']))
        os.system(' '.join(['cd', dir, '&&', 'git', 'commit', '-m', '"deployment of SO for tenant X"', '-a']))
        LOG.debug('Pushing new code to remote repository...')
        os.system(' '.join(['cd', dir, '&&', 'git', 'push']))

        shutil.rmtree(dir)


class ProvisionSOProcess(multiprocessing.Process):
    pass


class RetrieveSOProcess(multiprocessing.Process):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(RetrieveSOProcess, self).__init__(group, target, name, args, kwargs)
        self.entity = args[0]
        self.extras = args[1]
        repo_uri = self.entity.extras['repo_uri']
        self.host = urlparse(repo_uri).netloc.split('@')[1]

    def run(self):
        super(RetrieveSOProcess, self).run()
        self.so_details()

    # example request to the SO
    # curl -v -X GET http://localhost:8051/orchestrator/default \
    #   -H 'X-Auth-Token: '$KID \
    #   -H 'X-Tenant-Name: '$TENANT
    @conditional_decorator(timeit, DOING_PERFORMANCE_ANALYSIS)
    def so_details(self):
        LOG.info('Getting state of service orchestrator with: ' + self.host + '/orchestrator/default')
        heads = {
            'Content-Type': 'text/occi',
            'Accept': 'text/occi',
            'X-Auth-Token': self.extras['token'],
            'X-Tenant-Name': self.extras['tenant_name']}
        r = requests.get(HTTP + self.host + '/orchestrator/default', headers=heads)
        r.raise_for_status()

        attrs = r.headers['x-occi-attribute'].split(', ')
        for attr in attrs:
            kv = attr.split('=')
            if kv[0] != 'occi.core.id':
                if kv[1].startswith('"') and kv[1].endswith('"'):
                    kv[1] = kv[1][1:-1]  # scrub off quotes
                self.entity.attributes[kv[0]] = kv[1]
                LOG.debug('OCCI Attribute: ' + kv[0] + ' --> ' + kv[1])

        self.extras['ret_q'].put(self.entity.attributes)


class DestroySOProcess(multiprocessing.Process):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(DestroySOProcess, self).__init__(group, target, name, args, kwargs)
        self.entity = args[0]
        self.extras = args[1]
        self.nburl = CONFIG.get('cloud_controller', 'nb_api', '')
        repo_uri = self.entity.extras['repo_uri']
        self.host = urlparse(repo_uri).netloc.split('@')[1]

    def run(self):
        super(DestroySOProcess, self).run()
        self.dispose()

    # example request to the SO
    # curl -v -X DELETE http://localhost:8051/orchestrator/default \
    #   -H 'X-Auth-Token: '$KID \
    #   -H 'X-Tenant-Name: '$TENANT
    @conditional_decorator(timeit, DOING_PERFORMANCE_ANALYSIS)
    def dispose(self):
        # 1. dispose the active SO, essentially kills the STG/ITG
        # 2. dispose the resources used to run the SO
        url = HTTP + self.host + '/orchestrator/default'
        heads = {'X-Auth-Token': self.extras['token'],
                 'X-Tenant-Name': self.extras['tenant_name']}

        LOG.info('Disposing service orchestrator with: ' + url)
        r = requests.delete(url, headers=heads)
        r.raise_for_status()

        #TODO ensure that there is no conflict between location and term!

        url = self.nburl + self.entity.identifier.replace('/' + self.entity.kind.term + '/', '/app/')
        heads = {'Content-Type': 'text/occi',
                 'X-Auth-Token': self.extras['token'],
                 'X-Tenant-Name': self.extras['tenant_name']}
        LOG.info('Disposing service orchestrator container via CC... ' + url)
        _do_cc_request('DELETE', url, heads)

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

    if verb == 'POST':
        r = requests.post(url, headers=heads, auth=(user, pwd))
    elif verb == 'DELETE':
        r = requests.delete(url, headers=heads, auth=(user, pwd))
    elif verb == 'GET':
        r = requests.get(url, headers=heads, auth=(user, pwd))
    else:
        raise Exception('Unknown HTTP verb.')

    r.raise_for_status()
    return r
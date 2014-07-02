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
import os
import random
import requests
import shutil
import tempfile
from urlparse import urlparse

from mcn.sm import CONFIG
from mcn.sm import LOG
from mcn.sm import timeit, conditional_decorator, DOING_PERFORMANCE_ANALYSIS

# XXX: all URLs are hardcoded to 'http'

class SOManager():

    def __init__(self):
        self.nburl = CONFIG.get('cloud_controller', 'nb_api', '')
        if self.nburl == '':
            # XXX throw specific exception
            raise Exception('No nb_api paramter specified in sm.cfg')

        #scrub off any trailing slash
        if self.nburl[-1] == '/':
            self.nburl = self.nburl[0:-1]

        LOG.info('CloudController Northbound API: ' + self.nburl)

        if os.system('which git') != 0:
            raise EnvironmentError('Git is not available.')

    @conditional_decorator(timeit, DOING_PERFORMANCE_ANALYSIS)
    def deploy(self, entity, extras):

        entity.extras = {}

        LOG.debug('Ensuring SM SSH Key...')
        self.__ensure_ssh_key()

        # create an app for the new SO instance
        LOG.debug('Creating SO container...')
        repo_uri = self.__create_app(entity, extras)

        # get the code of the bundle and push it to the git facilities
        # offered by OpenShift
        LOG.debug('Deploying SO Bundle...')
        self.__deploy_app(repo_uri)

        host = urlparse(repo_uri).netloc.split('@')[1]
        entity.extras['host'] = host

        LOG.debug('Initialising the SO...')
        self.__init_so(entity, extras)

        # Deployment is done without any control by the client...
        # otherwise we won't be able to hand back a working service!
        LOG.debug('Deploying the SO bundle...')
        self.__deploy_so(entity, extras)

    def __init_so(self, entity, extras):
        host = entity.extras['host']
        url = 'http://' + host + '/action=init'
        heads = {'X-Auth-Token': extras['token'],
                 'X-Tenant-Name': extras['tenant_name']}
        LOG.debug('Initialising SO with: ' + url)
        # TODO: send `entity`'s attributes along with the call to deploy
        r = requests.post(url, headers=heads)
        r.raise_for_status()

    def __deploy_so(self, entity, extras):
        host = entity.extras['host']
        url = 'http://' + host + '/action=deploy'
        heads = {'X-Auth-Token': extras['token'],
                 'X-Tenant-Name': extras['tenant_name']}
        LOG.debug('Deploying SO with: ' + url)
        # TODO: make call to the SO's endpoint to execute the provision command
        r = requests.post(url, headers=heads)
        r.raise_for_status()

        # Store the stack id. This should not be shown to the EEU.
        if r.content == 'Please initialize SO with token and tenant first.':
            entity.attributes['mcn.service.state'] = 'failed'
            raise Exception('Error deploying the SO')
        else:
            LOG.debug('Heat stack id of service instance: ' + r.content)
            entity.extras['stack_id'] = r.content

    @conditional_decorator(timeit, DOING_PERFORMANCE_ANALYSIS)
    def dispose(self, entity, extras):
        # 1. dispose the active SO, essentially kills the STG/ITG
        # 2. dispose the resources used to run the SO
        host = entity.extras['host']
        url = 'http://' + host + '/action=dispose'
        heads = {'X-Auth-Token': extras['token'],
                 'X-Tenant-Name': extras['tenant_name']}

        LOG.info('Disposing service orchestrator with: ' + url)
        r = requests.post(url, headers=heads)
        r.raise_for_status()

        #TODO ensure that there is no conflict between location and term!
        url = self.nburl + entity.identifier.replace('/' + entity.kind.term + '/', '/app/')
        heads = {'Content-Type': 'text/occi',
                 'X-Auth-Token': extras['token'],
                 'X-Tenant-Name': extras['tenant_name']}
        LOG.info('Disposing service orchestrator container via CC... ' + url)
        self._do_cc_request('DELETE', url, heads)

    @conditional_decorator(timeit, DOING_PERFORMANCE_ANALYSIS)
    def so_details(self, entity, extras):

        import json
        host = entity.extras['host']

        LOG.info('Getting state of service orchestrator with: ' + host + '/state')
        r = requests.post('http://' + host + '/state')
        r.raise_for_status()
        details = json.loads(r.content)

        #service state model:
        #  - init
        #  - creating (deploy/provisioning)
        #  - active (entered into runtime ops)
        #  - destroying
        #  - failed

        #XXX this is a hack, will be removed with OCCI SO support
        if (type(details) == type('str')) or (type(details) == type(u'unicode')):
            LOG.debug('content:\n' + details)

            for detail in details.split(','):
                name_val = detail.split()[1].split('=')
                if name_val[0] != 'occi.core.id': #do not overwrite this attr
                    if name_val[1].startswith('"') and name_val[1].endswith('"'):
                        name_val[1] = name_val[1][1:-1] # scrub off quotes
                    LOG.debug('OCCI Attribute: ' + name_val[0] + '-->' + name_val[1])
                    entity.attributes[name_val[0]] = name_val[1]
        else:
            if details['state'] == u'CREATE_FAILED':
                entity.attributes['mcn.service.state'] = 'failed'
                LOG.error('Stack provisioning failed for: ' +
                          entity.extras['stack_id'])
            if details['state'] == u'CREATE_IN_PROGRESS':
                entity.attributes['mcn.service.state'] = 'creating'
                LOG.info('Stack creating...' + entity.extras['stack_id'])
            else:
                LOG.debug('Stack state: ' + details['state'])
                entity.attributes['mcn.service.state'] = 'active'

                #TODO ensure only the Kind-defined attributes are set
                for output_kv in details['output']:
                    LOG.debug('Setting OCCI attrib: ' + str(output_kv['output_key']) +
                              ' : ' + str(output_kv['output_value']))
                    entity.attributes[output_kv['output_key']] = output_kv['output_value']

    def _do_cc_request(self, verb, url, heads):
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

    def __create_app(self, entity, extras):

        # name must be A-Za-z0-9 and <=32 chars
        create_app_headers = {
            'Content-Type': 'text/occi',
            'Category': 'app; scheme="http://schemas.ogf.org/occi/platform#", '
            'python-2.7; scheme="http://schemas.openshift.com/template/app#", '
            'small; scheme="http://schemas.openshift.com/template/app#"',
            'X-OCCI-Attribute': 'occi.app.name=' + entity.kind.term[0:4] + 'srvinst' +
                                ''.join(random.choice('0123456789ABCDEF') for i in range(16))
            }

        #TODO requests should be placed on a queue as this is a blocking call
        url = self.nburl + '/app/'
        LOG.debug('Requesting container to execute SO Bundle: ' + self.nburl + '/app/')
        r = self._do_cc_request('POST', url, create_app_headers)

        loc = r.headers.get('Location', '')
        if loc == '':
            raise AttributeError("No OCCI Location attribute found in request")

        app_uri_path = urlparse(loc).path
        LOG.debug('SO container created: ' + app_uri_path)

        LOG.debug('Updating OCCI entity.identifier from: ' + entity.identifier + ' to: '
                  + app_uri_path.replace('/app/', entity.kind.location))
        entity.identifier = app_uri_path.replace('/app/', entity.kind.location)

        LOG.debug('Setting occi.core.id to: ' + app_uri_path.replace('/app/', ''))
        entity.attributes['occi.core.id'] = app_uri_path.replace('/app/', '')

        # get git uri. this is where our bundle is pushed to
        url = self.nburl + app_uri_path
        headers = {'Accept': 'text/occi'}
        r = self._do_cc_request('GET', url, headers)

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

    def __deploy_app(self, repo):
        """
            Deploy the local SO bundle
            assumption here
            - a git repo is returned
            - the bundle is not managed by git
        """
        # XXX: looks a lot like cc_deploy from mcn_cc :-) add (c)?

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
        # XXX the push takes time - place on queue
        os.system(' '.join(['cd', dir, '&&', 'git', 'push']))

        shutil.rmtree(dir)

    def __ensure_ssh_key(self):
        url = self.nburl + '/public_key/'
        heads = {'Accept': 'text/occi'}
        resp = self._do_cc_request('GET', url, heads)
        locs = resp.headers.get('x-occi-location', '')

        if len(locs.split()) < 1:
            LOG.debug('No SM SSH registered. Registering default SM SSH key.')
            occi_key_name, occi_key_content = self.__extract_public_key()

            create_key_headers = {'Content-Type': 'text/occi',
                'Category': 'public_key; scheme="http://schemas.ogf.org/occi/security/credentials#"',
                'X-OCCI-Attribute':'occi.key.name="' + occi_key_name + '", occi.key.content="' + occi_key_content + '"'
            }
            resp = self._do_cc_request('POST', url, create_key_headers)
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
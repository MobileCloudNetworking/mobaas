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

from distutils import dir_util
import os
import random
import shutil
import tempfile
from urlparse import urlparse

from mcn.sm import CONFIG
from mcn.sm import LOG
from mcn.sm import timeit, conditional_decorator, DOING_PERFORMANCE_ANALYSIS
import requests

class SOManager():

    def __init__(self):
        self.nburl = CONFIG.get('cloud_controller', 'nb_api')

        #scrub off any trailing slash
        if self.nburl[-1] == '/':
            self.nburl = self.nburl[0:-1]

        LOG.info('CloudController Northbound API: ' + self.nburl)

        if os.system('which git') != 0:
            raise EnvironmentError('Git is not available on the system path, or is not installed.')

    @conditional_decorator(timeit, DOING_PERFORMANCE_ANALYSIS)
    def deploy(self, entity, extras):
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

        LOG.debug('Initialising the SO...')
        self.__init_so(host, entity, extras)

        # Deployment is done without any control by the client...
        # otherwise we won't be able to hand back a working service!
        LOG.debug('Deploying the SO bundle...')
        self.__deploy_so(host, entity, extras)

    def __init_so(self, host, entity, extras):
        LOG.debug('Initialising SO with: ' + 'http://' + host + "/action=init")
        r = requests.post('http://' + host + "/action=init", headers={'Auth-Token': extras['token']})
        r.raise_for_status()

    def __deploy_so(self, host, entity, extras):
        # make call to the SO's endpoint to execute the provision command
        # XXX This call will eventually be an OCCI call
        LOG.debug('Deploying SO with: ' + 'http://' + host + '/action=deploy')
        r = requests.post('http://' + host + '/action=deploy', headers={'Auth-Token': extras['token']})
        r.raise_for_status()

    def dispose(self, entity, extras):
        # XXX does not call the dispose method of SO

        LOG.info('Disposing service instance: ' + ' FIXME!')
        host = ''
        # host = urlparse(repo_uri).netloc.split('@')[1]
        r = requests.post('http://' + host + '/action=dispose')
        r.raise_for_status()

        LOG.info('Disposing service orchestrator: ' + ' FIXME!')
        r = requests.delete(self.nburl + entity.identifier,
                            headers={'Content-Type': 'text/occi',
                                     'Auth-Token': extras['token']})
        r.raise_for_status()

        #TODO query for service instance management endpoints

    def so_details(self, entity, extras):
        pass

    def __create_app(self, entity, extras):
        '''
            create an app
            how if:
                SLA == bronze, size of gear should be small
                SLA == silver, size of gear should be medium
                SLA == gold, size of gear should be large
        '''

        # XXX app name random string is not guaranteed to be unique!
        create_app_headers = {'Content-Type': 'text/occi',
            'Category': 'app; scheme="http://schemas.ogf.org/occi/platform#", '
            'python-2.7; scheme="http://schemas.openshift.com/template/app#", '
            'small; scheme="http://schemas.openshift.com/template/app#"',
            'X-OCCI-Attribute': 'occi.app.name=serviceinstance' +
                                ''.join(random.choice('0123456789ABCDEF') for i in range(16))
            }

        LOG.debug('Requesting container to execute SO Bundle: ' + self.nburl + '/app/')
        #TODO requests should be placed on a queue as this is a blocking call
        r = requests.post(self.nburl + '/app/', headers=create_app_headers)
        r.raise_for_status()

        loc = r.headers.get('Location', '')
        if loc == '':
            raise AttributeError("No occi attributes found in request")

        app_uri_path = urlparse(loc).path
        LOG.debug('SO container created: ' + app_uri_path)

        # get git uri
        r = requests.get(self.nburl + app_uri_path, headers={'Accept': 'text/occi'})

        attrs = r.headers.get('X-OCCI-Attribute','')
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

        # create temp dir...and clone the remote repo provided by OpS
        dir = tempfile.mkdtemp()
        LOG.debug('Cloning git repository: ' + repo + ' to: ' + dir)
        cmd = ' '.join(['git', 'clone', repo, dir])
        os.system(cmd)

        # Get the SO bundle
        bundle_loc = CONFIG.get('service_manager', 'bundle_location')
        LOG.debug('Bundle to add to repo: ' + bundle_loc)
        dir_util.copy_tree(bundle_loc, dir)

        # put OpenShift stuff in place
        # build and pre_start_python comes from 'support' directory in bundle
        # XXX could be improved - e.g. could use from mako.template import Template?
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

        resp = requests.get(self.nburl + '/public_key/', headers={'Accept': 'text/occi'})
        resp.raise_for_status()
        locs = resp.headers.get('x-occi-location', '')

        if len(locs.split()) < 1:
            LOG.debug('No SM SSH registered. Registering default SM SSH key.')
            occi_key_name, occi_key_content = self._extract_public_key()

            create_key_headers = {'Content-Type': 'text/occi',
                'Category': 'public_key; scheme="http://schemas.ogf.org/occi/security/credentials#"',
                'X-OCCI-Attribute':'occi.key.name="' + occi_key_name + '", occi.key.content="' + occi_key_content + '"'
            }

            resp = requests.post(self.nburl + '/public_key/', headers=create_key_headers)
            resp.raise_for_status()
        else:
            LOG.debug('Valid SM SSH is registered with OpenShift.')

    def _extract_public_key(self):

        ssh_key_file = CONFIG.get('service_manager', 'ssh_key_location')
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



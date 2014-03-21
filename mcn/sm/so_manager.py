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

import httplib
import os
import shutil
import tempfile
from urlparse import urlparse

from mcn.sm import CONFIG

NBAPI_URL = CONFIG.get('cloud_controller', 'nb_api')

create_app_headers={'Content-Type': 'text/occi',
            'Category': 'app; scheme="http://schemas.ogf.org/occi/platform#", '
            'python-2.7; scheme="http://schemas.openshift.com/template/app#", '
            'small; scheme="http://schemas.openshift.com/template/app#"',
            }

class SOManager():

    def __init__(self):
        self.uri_app = ""
        nburl = urlparse(NBAPI_URL)
        self.conn = httplib.HTTPConnection(host=nburl.hostname, port=nburl.port)


    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # clean up connection
        self.conn.close()

    def deploy(self, entity, extras):
        # create an app for the new SO instance
        self.uri_app, repo_uri = self.create_app(entity)

        # get the code of the bundle and push it to the git facilities
        # offered by OpenShift
        self.deploy_app(repo_uri)

    def provision(self, entity, extras):
        # make call to the SO's endpoint to execute the provision command
        #TODO error handling
        self.conn.request('POST',
                          self.uri_app+"?action=provision",
                          headers={'Content-Type': 'text/occi',
                                   'Category': 'provision; scheme=""; kind="action"'})

    def dispose(self, entity, extras):
        #TODO error handling
        #TODO prob don't need self.uri_app - get it from entity
        self.conn.request('DELETE',
                          self.uri_app,
                          headers={'Content-Type': 'text/occi'})

    def so_details(self, entity):
        pass

    def create_app(self, entity):
        '''
            create an app
            how if:
                SLA == bronze, size of gear should be small
                SLA == silver, size of gear should be medium
                SLA == gold, size of gear should be large
        '''

        create_app_headers['X-OCCI-Attribute'] = 'occi.app.name=' + entity.identifier
        self.conn.request('POST', '/app/', headers=create_app_headers)
        resp = self.conn.getresponse()
        #TODO error handling
        app_uri_frag = resp.getheader('Location')

        # get git uri
        self.conn.request('GET', app_uri_frag, headers={'Accept: text/occi'})
        resp = self.conn.getresponse()
        attrs = resp.getheader('X-OCCI-Attribute')
        repo_uri = ''
        for attr in attrs.split(', '):
            if attr.find('occi.app.url') != -1:
                repo_uri = attr.split('=')[1]
            else:
                print('Oooops - no occi.app.url found!')

        return app_uri_frag, repo_uri

    def deploy_app(self, repo):
        """
        Deploy the local SO bundle
        assumption here
        - a git repo is returned
        - the bundle is not managed by git
        """

        #XXX assumes that git is installed
        if repo.startswith('git'):
            # create temp dir...and clone the remote repo provided by OpS
            dir = tempfile.mkdtemp()
            os.system(' '.join(['git', 'clone', repo, dir]))

                # Get the SO bundle
            bundle_loc = CONFIG.get('service_manager', 'bundle_location')
            shutil.copytree(bundle_loc, dir)

            # put OpenShift stuff in place
            # build and pre_start_python comes from 'support' directory in bundle
            # TODO this needs to be improved
            shutil.copyfile(bundle_loc+'/build', os.path.join(dir, '.openshift', 'action_hooks', 'build'))
            shutil.copyfile(bundle_loc+'/pre_start_python', os.path.join(dir, '.openshift', 'action_hooks', 'pre_start_python'))

            os.system(' '.join(['chmod', '+x', os.path.join(dir, '.openshift', 'action_hooks', '*')]))

            # add & push to OpenShift
            os.system(' '.join(['cd', dir, '&&', 'git', 'add', '-A']))
            os.system(' '.join(['cd', dir, '&&', 'git', 'commit', '-m', '"deployment of SO for tenant X"', '-a']))
            os.system(' '.join(['cd', dir, '&&', 'git', 'push']))

        else:
            print('oopppssss - I do not know how to deploy here!')

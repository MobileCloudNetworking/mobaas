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
import shutil
import os
import tempfile

from mcn import SORegistry


class SOManager():

    def __init__(self):
        self.so_reg = SORegistry.SORegistry()
        self.uri_app = ""
        self.NBAPI_URL = 'http://localhost:8000'
        self.conn = httplib.HTTPConnection(self.NBAPI_URL)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.conn.close()

    def deploy(self, entity):
        """
        Make sure app for deploying SO bundle is up!
        """
        # make a home for the SO instance
        self.uri_app, repo = self.create_app()

        dir = self.prep_app(repo)
        self.deploy_app(dir)

    def provision(self, entity):
        pass

    def dispose(self, service_instance_id):
        self.conn.request('DELETE', '')
        pass

    def getSO(self, service_instance_id):
        self.so_reg.get_resource(service_instance_id)

    def create_app(self):
        # create an app

        self.conn.request('POST', '/app', headers={'Content-Type': 'text/occi',
                                              'Category': 'app; scheme="http://schemas.ogf.org/occi/platform#", '
                                                          'python-2.7; scheme="http://schemas.openshift.com/template/app#", '
                                                          'medium; scheme="http://schemas.openshift.com/template/app#"',
                                              'X-OCCI-Attribute': 'occi.app.name=TEST_APP'}) # + so_bundle_id['name']
        resp = self.conn.getresponse()
        #TODO error handling
        uri_app = resp.getheader('Location')
        self.conn.close()

        # get git uri
        self.conn.request('GET', uri_app, headers={'Accept: text/occi'})
        resp = self.conn.getresponse()
        attrs = resp.getheader('X-OCCI-Attribute')
        repo = ''
        for attr in attrs.split(', '):
            if attr.find('occi.app.url') != -1:
                repo = attr.split('=')[1]
        self.conn.close()

        return uri_app, repo

    @property
    def prep_app(repo):
        """
        Prep local SO bundle
        """
        # create temp dir...and clone
        dir = tempfile.mkdtemp()
        os.system(' '.join('git', 'clone', repo, dir))

        # put stuff in place
        shutil.copytree('../sample_so', dir)
        shutil.copyfile('pre_build', os.path.join(dir, '.openshift', 'action_hooks', 'pre_build'))
        return dir

    def deploy_app(dir):
        """
        Fire it all up!
        """
        os.system(' '.join('cd', dir, '&&', 'git', 'push'))

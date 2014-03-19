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

class SOManager():

    def __init__(self):
        self.uri_app = ""
        #TODO extract and place in a config file
        self.NBAPI_URL = 'http://localhost:8000'
        self.conn = httplib.HTTPConnection(self.NBAPI_URL)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # clean up connection
        self.conn.close()

    def deploy(self, entity):
        # create an app for the new SO instance
        self.uri_app, repo = self.create_app()

        # get the code of the bundle and push it to the git facilities
        # offered by OpenShift
        dir = self.prep_app(repo)
        self.deploy_app(dir)

    def provision(self, entity):
        # make call to the SO's endpoint to execute the provision command
        pass

    def dispose(self, service_instance_id):
        #TODO error handling
        self.conn.request('DELETE', self.NBAPI_URL+self.uri_app, headers={'Content-Type': 'text/occi'})

    # def getSO(self, service_instance_id):
    #     self.so_reg.get_resource(service_instance_id)

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
        # push to OpenShift
        os.system(' '.join('cd', dir, '&&', 'git', 'push'))

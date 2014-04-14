#   Copyright (c) 2013-2015, Intel Performance Learning Solutions Ltd, Intel Corporation.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Sample SO.
"""

import os
import threading

from sdk.mcn import util

HERE = os.environ.get('OPENSHIFT_REPO_DIR', '.')


class ServiceOrchstratorExecution(object):
    """
    Sample SO execution part.
    """

    def __init__(self, token):
        # read template...
        self.token = token
        f = open(os.path.join(HERE, 'data', 'test.yaml'))
        self.template = f.read()
        f.close()
        self.stack_id = None
        # make sure we can talk to deployer...
        self.deployer = util.get_deployer(self.token, url_type='public')

    def design(self):
        """
        Do initial design steps here.
        """
        pass

    def deploy(self):
        """
        deploy SICs.
        """
        if self.stack_id is None:
            self.stack_id = self.deployer.deploy(self.template, self.token)

    def provision(self):
        """
        (Optional) if not done during deployment - provision.
        """
        pass

    def dispose(self):
        """
        Dispose SICs.
        """
        if self.stack_id is not None:
            self.deployer.dispose(self.stack_id, self.token)
            self.stack_id = None

    def state(self):
        """
        Report on state.
        """
        if self.stack_id is not None:
            tmp = self.deployer.details(self.stack_id, self.token)
            if tmp['state'] != 'CREATE_COMPLETE':
                return 'Stack is currently being deployed...'
            else:
                return 'All good - Stack id is: ' + str(self.stack_id) + \
                       ' - Output is: ' + str(tmp['output'][0]['output_value'])
        else:
            return 'Stack is not deployed atm.'


class ServiceOrchstratorDecision(object):
    """
    Sample Decision part of SO.
    """

    def __init__(self, so_e, token):
        self.so_e = so_e
        self.token = token

    def run(self):
        """
        Decision part implementation goes here.
        """
        pass


class ServiceOrchstrator(object):
    """
    Sample SO.
    """

    def __init__(self, token):
        self.so_e = ServiceOrchstratorExecution(token)
        self.so_d = ServiceOrchstratorDecision(self.so_e, token)
        # so_d.start()

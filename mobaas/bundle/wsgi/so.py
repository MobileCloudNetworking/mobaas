#   Copyright (c) 2013-2015, Intel Performance Learning Solutions Ltd, Intel Corporation.
#   Copyright 2015 Zuercher Hochschule fuer Angewandte Wissenschaften
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

import logging
import os
import threading

from sdk.mcn import util

HERE = os.environ['OPENSHIFT_REPO_DIR']


def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(threadName)s \t %(levelname)s %(asctime)s: \t%(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

LOG = config_logger()


class ServiceOrchestratorExecution():
    """
    Sample SO execution part.
    """
    def __init__(self, token, tenant, ready_event):
        self.token = token
        self.tenant_name = tenant
        self.event = ready_event
        f = open(os.path.join(HERE, 'data', 'mobaas.yaml'))
        self.template = f.read()
        f.close()
        self.endpoint = None
        self.stack_id = None
        self.region_name = 'UBern'
        #self.deployer = util.get_deployer(self.token, url_type='public', tenant_name=self.tenant_name)
        self.deployer = util.get_deployer(self.token, url_type='public', tenant_name=self.tenant_name, region=self.region_name)

    def design(self):
        """
        Do initial design steps here.
        """
        LOG.debug('Executing design logic')

    def deploy(self):
        """
        deploy SICs.
        """
        LOG.debug('Executing deployment logic')
        if self.stack_id is None:
            self.stack_id = self.deployer.deploy(self.template, self.token)

    def provision(self):
        """
        (Optional) if not done during deployment - provision.
        """
        # TODO add you provision phase logic here
        #
        LOG.debug('Executing provisioning logic')
        # once logic executes, deploy phase is done
        self.event.set()

    def dispose(self):
        """
        Dispose SICs.
        """
        LOG.debug('Executing disposal logic')
        if self.stack_id is not None:
            self.deployer.dispose(self.stack_id, self.token)
            self.stack_id = None
        # TODO on disposal, the SOE should notify the SOD to shutdown its thread

    def state(self):
        """
        Report on state.
        """
        LOG.debug('Executing state retrieval logic')
        if self.stack_id is not None:
            tmp = self.deployer.details(self.stack_id, self.token)
            #if tmp['output'] is not None:
            if tmp.get('output', None) is not None:
                for i in tmp['output']:
                    if i['output_key'] == 'mcn.endpoint.mobaas':
                        self.endpoint = 'http://' + str(i['output_value']) + ':5000'
			i['output_value'] = self.endpoint
                        print 'Endpoint is: ' + self.endpoint
                return tmp['state'], self.stack_id, tmp['output']
            else:
		return tmp['state'], self.stack_id, None
        return 'Unknown', 'N/A'

    # This is not part of the SOE interface
    def update(self, updated_service):
        # TODO implement your own update logic - this could be a heat template update call
        pass


class ServiceOrchestratorDecision(threading.Thread):
    """
    Sample Decision part of SO.
    """

    def __init__(self, so_e, token, ready_event):
        super(ServiceOrchestratorDecision, self).__init__()
        self.so_e = so_e
        self.token = token
        self.event = ready_event

    def run(self):
        """
        Decision part implementation goes here.
        """
        # it is unlikely that logic executed will be of any use until the provisioning phase has completed

        LOG.debug('Waiting for deploy and provisioning to finish')
        self.event.wait()
        LOG.debug('Starting runtime logic...')
        # TODO implement you runtime logic here - you should probably release the locks afterwards, maybe in stop ;-)


class ServiceOrchestrator(object):
    """
    Sample SO.
    """

    def __init__(self, token, tenant):
        # this python thread event is used to notify the SOD that the runtime phase can execute its logic
        self.event = threading.Event()
        self.so_e = ServiceOrchestratorExecution(token, tenant, self.event)
        self.so_d = ServiceOrchestratorDecision(self.so_e, token, self.event)
        LOG.debug('Starting SOD thread...')
        self.so_d.start()


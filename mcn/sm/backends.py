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

import logging
import multiprocessing
from occi.backend import ActionBackend, KindBackend

from mcn.sm.so_manager import CreateSOProcess
from mcn.sm.so_manager import DeploySOProcess
from mcn.sm.so_manager import RetrieveSOProcess
from mcn.sm.so_manager import DestroySOProcess

#service state model:
#  - init
#  - creating (deploy/provisioning)
#  - active (entered into runtime ops)
#  - destroying
#  - failed


class ServiceBackend(KindBackend, ActionBackend):
    '''
    Provides the basic functionality required to CRUD SOs
    '''

    def __init__(self):
        multiprocessing.log_to_stderr(logging.DEBUG)
        self.ret_q = multiprocessing.Queue()

    def create(self, entity, extras):
        super(ServiceBackend, self).create(entity, extras)

        # set the return value queue
        extras['ret_q'] = self.ret_q

        # run the process
        tcp = CreateSOProcess(args=(entity, extras, ))
        tcp.start()
        tcp.join()

        # update the newly created container's IDs
        ret_vals = self.ret_q.get()
        entity.identifier = ret_vals['identifier']

        # pass the repo URI to the deploy process, no join() needed
        entity.extras = {'repo_uri': ret_vals['repo_uri']}
        dp = DeploySOProcess(args=(entity, extras, ))
        dp.start()

    def retrieve(self, entity, extras):
        super(ServiceBackend, self).retrieve(entity, extras)

        # set the return value queue
        extras['ret_q'] = self.ret_q

        # run the process
        rp = RetrieveSOProcess(args=(entity, extras, ))
        rp.start()
        rp.join()

        # set the entity's attributes
        entity.attributes = extras['ret_q'].get()
        print entity.attributes

    def update(self, old, new, extras):
        raise NotImplementedError()

    def replace(self, old, new, extras):
        raise NotImplementedError()

    def delete(self, entity, extras):
        super(ServiceBackend, self).delete(entity, extras)
        dp = DestroySOProcess(args=(entity, extras, ))
        # we don't have to block here => no join()
        dp.start()

    # currently not exposed on the kind
    def action(self, entity, action, attributes, extras):
        raise NotImplementedError()
        # super(ServiceBackend, self).action(entity, action, attributes, extras)
        # if action == 'provision':
        #     #pass service_instance_id here
        #     self.som.provision(entity, extras)

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

from occi.backend import ActionBackend, KindBackend

from mcn.sm.processes_manager import ProMgr
from mcn.sm.processes_manager import StateUpdater
from mcn.sm.so_manager import CreateSOProcess
from mcn.sm.so_manager import DeploySOProcess
from mcn.sm.so_manager import RetrieveSOProcess
from mcn.sm.so_manager import DestroySOProcess

#service state model:
#  - init
#  - creating
#  - deploying
#  - provisioning
#  - active (entered into runtime ops)
#  - destroying
#  - failed


class ServiceBackend(KindBackend, ActionBackend):
    """
    Provides the basic functionality required to CRUD SOs
    """

    def __init__(self, app):
        self.god_orch = ProMgr()
        self.god_orch.run()
        self.state_updater = StateUpdater(self.god_orch.deploy_ret_vals, app.registry)
        self.state_updater.start()

    def create(self, entity, extras):
        super(ServiceBackend, self).create(entity, extras)

        entity.attributes['mcn.service.state'] = 'init'

        # put the task on the queue and have it processed
        self.god_orch.create_tasks.put(CreateSOProcess(entity, extras))
        # when processed get the results
        ret_vals = self.god_orch.create_ret_vals.get()

        # update the entity
        t_entity = ret_vals[0]['entity']
        entity.attributes = t_entity.attributes
        entity.identifier = t_entity.identifier
        entity.attributes['mcn.service.state'] = 'creating'

        # pass the repo URI to the deploy process
        entity.extras = {'repo_uri': ret_vals[0]['repo_uri']}
        self.god_orch.deploy_tasks.put(DeploySOProcess(entity, extras))

    def retrieve(self, entity, extras):
        super(ServiceBackend, self).retrieve(entity, extras)

        # run the process
        self.god_orch.retrieve_tasks.put(RetrieveSOProcess(entity, extras))
        ret_vals = self.god_orch.retrieve_ret_vals.get()

        # set the entity's attributes
        entity.attributes = ret_vals[0]['entity'].attributes

    def delete(self, entity, extras):
        super(ServiceBackend, self).delete(entity, extras)
        entity.attributes['mcn.service.state'] = 'destroying'
        self.god_orch.destroy_tasks.put(DestroySOProcess(entity, extras))

    def update(self, old, new, extras):
        raise NotImplementedError()

    def replace(self, old, new, extras):
        raise NotImplementedError()

    # currently not exposed on the kind
    def action(self, entity, action, attributes, extras):
        raise NotImplementedError()
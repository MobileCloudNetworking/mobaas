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

from mcn.sm.so_manager import AsychExe
from mcn.sm.so_manager import CreateSOTask
from mcn.sm.so_manager import ActivateSOTask
from mcn.sm.so_manager import DeploySOTask
from mcn.sm.so_manager import ProvisionSOTask
from mcn.sm.so_manager import RetrieveSOTask
from mcn.sm.so_manager import DestroySOTask

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
        self.registry = app.registry

    def create(self, entity, extras):
        super(ServiceBackend, self).create(entity, extras)
        # create the python container
        entity, extras = CreateSOTask(entity, extras).run()
        # run background tasks
        bg_tasks = AsychExe(self.registry, [ActivateSOTask(entity, extras), DeploySOTask(entity, extras),
                                            ProvisionSOTask(entity, extras)])
        bg_tasks.start()

    def retrieve(self, entity, extras):
        super(ServiceBackend, self).retrieve(entity, extras)
        entity, extras = RetrieveSOTask(entity, extras).run()

    def delete(self, entity, extras):
        super(ServiceBackend, self).delete(entity, extras)
        DestroySOTask(entity, extras).run()

    def update(self, old, new, extras):
        raise NotImplementedError()

    def replace(self, old, new, extras):
        raise NotImplementedError()

    # currently not exposed on the kind
    def action(self, entity, action, attributes, extras):
        raise NotImplementedError()
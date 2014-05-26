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

from mcn.sm.so_manager import SOManager

class ServiceBackend(KindBackend, ActionBackend):
    '''
    Provides the basic functionality required to CRUD SOs

    Will implement create, retrieve, update, delete, replace
    Will also implement: action (from ActionBackend).
    '''
    def __init__(self):
        self.som = SOManager()

    def create(self, entity, extras):
        super(ServiceBackend, self).create(entity, extras)
        self.som.deploy(entity, extras)

    def retrieve(self, entity, extras):
        super(ServiceBackend, self).retrieve(entity, extras)
        #TODO understand if we need to refresh details from the SO
        # if so then the retrieve needs to update details!

    def update(self, old, new, extras):
        super(ServiceBackend, self).update(old, new, extras)
        #TODO
        raise NotImplementedError()

    def replace(self, old, new, extras):
        super(ServiceBackend, self).replace(old, new, extras)
        #TODO
        raise NotImplementedError()

    def delete(self, entity, extras):
        super(ServiceBackend, self).delete(entity, extras)
        raise NotImplementedError()
        #self.som.dispose(entity, extras)

    # currently not exposed on the kind
    def action(self, entity, action, attributes, extras):
        super(ServiceBackend, self).action(entity, action, attributes, extras)

        if action == 'provision':
            #pass service_instance_id here
            self.som.provision(entity, extras)

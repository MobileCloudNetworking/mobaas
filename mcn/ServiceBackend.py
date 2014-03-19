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
from mcn import SOManager

# SO* classes to be extracted elsewhere
class ServiceBackend(KindBackend, ActionBackend):
    '''
    Provides the basic functionality required to CRUD SOs

    Will implement create, retrieve, update, delete, replace
    Will also implement: action (from ActionBackend).
    '''
    def __init__(self):
        self.som = SOManager.SOManager()

    def create(self, entity, extras):
        super(ServiceBackend, self).create(entity, extras)

        #self.som.deploy(entity)

    def retrieve(self, entity, extras):
        super(ServiceBackend, self).retrieve(entity, extras)

        #TODO understand if we need to refresh details from the SO
        # if so then the retrieve needs to update details!

    def update(self, old, new, extras):
        super(ServiceBackend, self).update(old, new, extras)

    def replace(self, old, new, extras):
        super(ServiceBackend, self).replace(old, new, extras)
        #changes to the service need done here via SO of instance

    def delete(self, entity, extras):
        super(ServiceBackend, self).delete(entity, extras)
        #pass service_instance_id
        self.som.dispose()

    def action(self, entity, action, attributes, extras):
        super(ServiceBackend, self).action(entity, action, attributes, extras)

        if action == 'provision':
            #pass service_instance_id here
            self.som.provision(entity)

# Backend to manage bundles - only admins should have access to this
class BundleBackend(KindBackend, ActionBackend):
    def __init__(self):
        super(BundleBackend, self).__init__()

    def action(self, entity, action, attributes, extras):
        super(BundleBackend, self).action(entity, action, attributes, extras)

    def delete(self, entity, extras):
        super(BundleBackend, self).delete(entity, extras)

    def retrieve(self, entity, extras):
        super(BundleBackend, self).retrieve(entity, extras)

    def replace(self, old, new, extras):
        super(BundleBackend, self).replace(old, new, extras)

    def create(self, entity, extras):
        super(BundleBackend, self).create(entity, extras)

    def update(self, old, new, extras):
        super(BundleBackend, self).update(old, new, extras)
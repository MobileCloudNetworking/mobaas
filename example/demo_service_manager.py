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
from mcn.sm.service import Service

__author__ = 'andy'

from occi.backend import MixinBackend
from occi.core_model import Kind as Type
from occi.core_model import Mixin as SLA
from occi.core_model import Resource
from occi.wsgi import Application


# IGNORE THIS
# Ideally this dummy SLA backend will be generic based on the WP5 work
class EpcSLABackend(MixinBackend):

    def __init__(self):
        super(EpcSLABackend, self).__init__()

    def delete(self, entity, extras):
        super(EpcSLABackend, self).delete(entity, extras)

    def retrieve(self, entity, extras):
        super(EpcSLABackend, self).retrieve(entity, extras)

    def replace(self, old, new, extras):
        super(EpcSLABackend, self).replace(old, new, extras)

    def create(self, entity, extras):
        super(EpcSLABackend, self).create(entity, extras)

    def update(self, old, new, extras):
        super(EpcSLABackend, self).update(old, new, extras)


if __name__ == '__main__':

    # defines the service to offer - the service owner defines this
    epc_svc_type = Type('http://schemas.mobile-cloud-networking.eu/occi/sm#',
                  'epc',
                  title='This is an example service type - EPC',
                  attributes={'mcn.endpoint.enodeb':    'immutable',
                              'mcn.endpoint.mme':       'immutable',
                              'mcn.endpoint.hss':       'immutable',
                              'mcn.endpoint.srv-gw':    'immutable',
                              'mcn.endpoint.pdn-gw':    'immutable',
                              },
                  related=[Resource.kind],
                  actions=[])

    # Create a service
    srv = Service(Application(), epc_svc_type)

    #Add some example extensions. These are OCCI Mixins with a backend
    dummy_sla_backend = EpcSLABackend()
    srv.register_extension(SLA('http://schemas.mobile-cloud-networking.eu/occi/sla#', 'bronze'), dummy_sla_backend)
    srv.register_extension(SLA('http://schemas.mobile-cloud-networking.eu/occi/sla#', 'silver'), dummy_sla_backend)
    srv.register_extension(SLA('http://schemas.mobile-cloud-networking.eu/occi/sla#', 'gold'), dummy_sla_backend)

    # Run the service manager
    srv.run()


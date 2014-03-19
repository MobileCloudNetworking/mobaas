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

from occi.registry import NonePersistentRegistry

class SORegistry(NonePersistentRegistry):

#dummy class
    def __init__(self):
        super(SORegistry, self).__init__()

    def get_default_type(self):
        return super(SORegistry, self).get_default_type()

    def get_backend(self, category, extras):
        return super(SORegistry, self).get_backend(category, extras)

    def get_resource(self, key, extras):
        return super(SORegistry, self).get_resource(key, extras)

    def add_resource(self, key, resource, extras):
        super(SORegistry, self).add_resource(key, resource, extras)

    def set_renderer(self, mime_type, renderer):
        return super(SORegistry, self).set_renderer(mime_type, renderer)

    def get_extras(self, extras):
        super(SORegistry, self).get_extras(extras)

    def get_renderer(self, mime_type):
        return super(SORegistry, self).get_renderer(mime_type)

    def get_resource_keys(self, extras):
        return super(SORegistry, self).get_resource_keys(extras)

    def get_all_backends(self, entity, extras):
        return super(SORegistry, self).get_all_backends(entity, extras)

    def delete_mixin(self, mixin, extras):
        super(SORegistry, self).delete_mixin(mixin, extras)

    def get_category(self, path, extras):
        return super(SORegistry, self).get_category(path, extras)

    def get_categories(self, extras):
        return super(SORegistry, self).get_categories(extras)

    def get_resources(self, extras):
        return super(SORegistry, self).get_resources(extras)

    def get_hostname(self):
        return super(SORegistry, self).get_hostname()

    def delete_resource(self, key, extras):
        super(SORegistry, self).delete_resource(key, extras)

    def set_backend(self, category, backend, extras):
        super(SORegistry, self).set_backend(category, backend, extras)
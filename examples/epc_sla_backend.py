from occi.backend import MixinBackend


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
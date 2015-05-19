__author__ = 'florian'

import unittest
from occi.backend import ActionBackend, KindBackend
from sm.sm.backends import ServiceBackend
from mock import patch
from sm.sm.so_manager import SOManager
from occi.core_model import Kind
from occi.core_model import Resource

@patch('mcn.sm.so_manager.CONFIG')
@patch('mcn.sm.so_manager.LOG')
class TestBackendsConstruction(unittest.TestCase):

    def setUp(self):
        pass

    @patch('os.system')
    @patch('mcn.sm.so_manager.SOManager', spec='mcn.sm.so_manager.SOManager')
    def test_init_for_sanity(self, mock_som, mock_os, mock_log, mock_config):
        mock_os.return_value = 0
        self.service_backend = ServiceBackend()
        # Test that service_backend contains a SOManager instance
        self.assertEqual(self.service_backend.som.__class__, SOManager)

        # assertInstance should work there
        # self.assertIsInstance(self.service_backend.som, SOManager)
        # print type(self.service_backend.som)


class TestBackendsMethods(unittest.TestCase):

    def setUp(self):
        kind = Kind('http://schemas.mobile-cloud-networking.eu/occi/sm#',
                    'myservice',
                    title='Test Service',
                    attributes={'mcn.test.attribute1': 'immutable'},
                    related=[Resource.kind],
                    actions=[])
        self.test_entity = Resource('my-id', kind, None)
        self.patcher_system = patch('os.system', return_value=0)
        self.patcher_system.start()
        self.patcher_config = patch('mcn.sm.so_manager.CONFIG')
        self.patcher_config.start()
        self.patcher_log = patch('mcn.sm.so_manager.LOG')
        self.patcher_log.start()
    #     Check why service backend cannot be created there with a mock (mock not taken into account)


    @patch('mcn.sm.so_manager.SOManager.deploy')
    def test_create_for_sanity(self, mock_deploy):
        self.service_backend = ServiceBackend()
        self.service_backend.create(self.test_entity, None)
        mock_deploy.assert_called_once_with(self.test_entity, None)

    @patch('mcn.sm.so_manager.SOManager.so_details')
    def test_retrieve_for_sanity(self, mock_so_details):
        service_backend = ServiceBackend()
        service_backend.retrieve(self.test_entity, None)
        mock_so_details.assert_called_once_with(self.test_entity, None)

    @patch('mcn.sm.so_manager.SOManager.dispose')
    def test_delete_for_sanity(self, mock_dispose):
        service_backend = ServiceBackend()
        service_backend.delete(self.test_entity, None)
        mock_dispose.assert_called_once_with(self.test_entity, None)

    # def testNotImplemented(self):
    #     service_backend = ServiceBackend()
    #     # self.assertRaises(NotImplementedError, service_backend.update(None, None, None))
    #     self.assertRaises(NotImplementedError, service_backend.replace(None, None, None))

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_log.stop()
        self.patcher_system.stop()


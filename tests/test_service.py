import unittest
from occi.backend import ActionBackend, KindBackend
from sm.sm.service import Service, MCNApplication
from sm.sm.backends import ServiceBackend
from mock import patch
from sm.sm.so_manager import SOManager
from occi.core_model import Kind
from occi.core_model import Resource
from mock import Mock, MagicMock
from wsgiref.simple_server import make_server


class TestServiceConstruction(unittest.TestCase):
    # Constants
    DESIGN_URI = 'd.uri'
    SERVICE_TOKEN = 's.token'
    SERVICE_TENANT_NAME = 's.tenant.name'
    REGION = ''
    SERVICE_ENDPOINT = 's.endpoint'

    # Side_effect methods for mock.sm.so_manager.CONFIG
    def side_effect_config(self, *args):
        if args[0] == 'service_manager':
            if args[1] == 'design_uri':
                return self.DESIGN_URI
        if args[0] == 'service_manager_admin':
            if args[1] == 'service_token':
                return self.SERVICE_TOKEN
            if args[1] == 'service_tenant_name':
                return self.SERVICE_TENANT_NAME
            if args[1] == 'region':
                return self.REGION
            if args[1] == 'service_endpoint':
                return self.SERVICE_ENDPOINT
            if args[1] == 'register_service':
                return True
        if args[0] == 'general':
            if args[1] == 'port':
                return '8888'

    def setUp(self):
        self.patcher_config = patch('mcn.sm.Service.CONFIG')
        self.patcher_config.start()
        self.patcher_config_get = patch('mcn.sm.Service.CONFIG.get', side_effect=self.side_effect_config)
        self.patcher_config_get.start()
        self.patcher_log = patch('mcn.sm.Service.LOG')
        self.patcher_log.start()
        self.patcher_system = patch('os.system', return_value=0)
        self.patcher_system.start()
        self.epc_svc_type = Kind('http://schemas.mobile-cloud-networking.eu/occi/sm#',
                                 'epc',
                                 title='This is an example EPC service type',
                                 attributes={'mcn.endpoint.enodeb': 'immutable',
                                             'mcn.endpoint.mme': 'immutable',
                                             'mcn.endpoint.hss': 'immutable',
                                             'mcn.endpoint.srv-gw': 'immutable',
                                             'mcn.endpoint.pdn-gw': 'immutable',
                                 },
                                 related=[Resource.kind],
                                 actions=[])

    @patch('mcn.sm.backends.ServiceBackend')
    def test_init_for_sanity(self, mock_sb):
        service = Service(MCNApplication(), self.epc_svc_type)
        self.assertEqual(service.srv_type, self.epc_svc_type)
        # mock_sb.assert_called_once_with()


    @patch('mcn.sm.Service.LOG.debug')
    @patch('keystoneclient.v2_0.client.Client')
    @patch('sdk.mcn.util.services.get_service_endpoint')
    def test_register_service(self, mock_serv_endpoint_get, mock_client_constructor, mock_log):
        #Init
        ##Child mocks
        service_id = '101'
        mock_service_create = Mock(id=service_id)

        endpoint_id = '999'
        endpoint_region = 'RegionOne'
        endpoint_public_url = 'http://my.endpoint'
        mock_endpoint_create = Mock(id=endpoint_id, region=endpoint_region, publicurl=endpoint_public_url)

        attrs = {'services.create.return_value': mock_service_create,
                 'endpoints.create.return_value': mock_endpoint_create}
        mock_keystone_object = Mock(id=1, **attrs)

        ##return values
        mock_serv_endpoint_get.return_value = ''
        mock_client_constructor.return_value = mock_keystone_object

        #Calls
        service = Service(MCNApplication(), self.epc_svc_type)
        service.register_service(self.epc_svc_type)

        #Asserts
        mock_serv_endpoint_get.assert_called_once_with(tenant_name=self.SERVICE_TENANT_NAME, token=self.SERVICE_TOKEN,
                                                       identifier='epc', endpoint=self.DESIGN_URI,
                                                       url_type='public')
        mock_client_constructor.assert_called_once_with(tenant_name=self.SERVICE_TENANT_NAME, token=self.SERVICE_TOKEN,
                                                        auth_url=self.DESIGN_URI)
        mock_log.assert_called_with(
            'Service is now registered with keystone: ID: ' + endpoint_id + ' Region: ' +
            endpoint_region + ' Public URL: ' + endpoint_public_url + ' Service ID: ' + service_id)

    @patch('mcn.sm.Service.make_server')
    @patch('mcn.sm.Service.Service.register_service')
    @patch('mcn.sm.Service.MCNApplication.register_backend')
    def test_run(self, mock_register_backend, mock_register_service, mock_makeserver):
        #Inits
        mock_serv_forever = MagicMock()
        mock_makeserver.return_value = mock_serv_forever

        #Runs
        app = MCNApplication()
        service = Service(app, self.epc_svc_type)
        service.run()

        #Asserts
        mock_register_service.assert_called_once_with(self.epc_svc_type)
        mock_register_backend.assert_called_once_with(self.epc_svc_type, service.service_backend)
        mock_makeserver.assert_called_once_with('', 8888, app)
        mock_serv_forever.serve_forever.assert_called_once_with()

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_log.stop()
        self.patcher_system.stop()
        self.patcher_config_get.stop()
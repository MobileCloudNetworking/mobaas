import unittest, nose, os
from mock import patch, call, mock_open
import httpretty
from occi.core_model import Kind
from occi.core_model import Resource


if 'SM_CONFIG_PATH' not in os.environ or 'SM_TIMEIT' not in os.environ:
    raise AttributeError('Please provide SM_CONFIG_PATH, SM_TIMEIT as env vars.')
from sm.sm import so_manager

# Testing Constructor

@patch('mcn.sm.so_manager.CONFIG')
@patch('mcn.sm.so_manager.LOG')
class TestSOMConstruction(unittest.TestCase):
    @patch('os.system')
    def test_proper_init_sanity(self, mock_os_system, mock_log, mock_config):
        mock_log.return_value = True
        mock_config.get.return_value = 'http://cc.cloudcomplab.ch:8888'
        mock_os_system.return_value = 0

        som = so_manager.SOManager()
        self.assertEqual(som.nburl, 'http://cc.cloudcomplab.ch:8888')
        mock_os_system.assert_called_with('which git')


    @patch('os.system')
    def test_init_nogit(self, mock_os_system, mock_log, mock_config):
        mock_os_system.return_value = 1
        self.assertRaises(EnvironmentError, so_manager.SOManager)


# Testing Methods

class TestSOMmethods(unittest.TestCase):
    CC_USER = 'user'
    CC_PWD = 'pwd'
    CC_NB_API = 'http://localhost:8888'
    CC_SM_BL = 'so/bundle'
    CC_SM_SSH = 'key.is.here.'

    # Side_effect methods for mock.sm.so_manager.CONFIG
    def side_effect_config(self, *args):
        if args[0] == 'cloud_controller':
            if args[1] == 'user':
                return self.CC_USER
            if args[1] == 'pwd':
                return self.CC_PWD
            if args[1] == 'nb_api':
                return self.CC_NB_API
        if args[0] == 'service_manager':
            if args[1] == 'bundle_location':
                return self.CC_SM_BL
            if args[1] == 'ssh_key_location':
                return self.CC_SM_SSH

    def setUp(self):
        self.patcher_config = patch('mcn.sm.so_manager.CONFIG')
        self.patcher_config.start()
        self.patcher_config_get = patch('mcn.sm.so_manager.CONFIG.get', side_effect=self.side_effect_config)
        self.patcher_config_get.start()
        self.patcher_log = patch('mcn.sm.so_manager.LOG')
        self.patcher_log.start()
        self.patcher_system = patch('os.system', return_value=0)
        self.patcher_system.start()
        self.som = so_manager.SOManager()
        self.som.nburl = 'http://localhost:8888'


    @patch('mcn.sm.so_manager.SOManager._SOManager__extract_public_key')
    @patch('mcn.sm.so_manager.SOManager._do_cc_request')
    def test_ensure_ssh_key_absent(self, mock_cc, mock_extract):
        # Initialization
        # Load a key by mocking the extract_public_key call
        mock_extract.return_value = ('my_key', '123456789123456789')

        # Test method
        #Check key
        self.som._SOManager__ensure_ssh_key()
        expected = [call('GET', 'http://localhost:8888/public_key/', {'Accept': 'text/occi'}),
                    call('POST', 'http://localhost:8888/public_key/',
                         {'Category': 'public_key; scheme="http://schemas.ogf.org/occi/security/credentials#"',
                          'X-OCCI-Attribute': 'occi.key.name="my_key",'
                                              ' occi.key.content="123456789123456789"',
                          'Content-Type': 'text/occi'
                         }
                    )]

        # Asserts
        #Check if the CC mock has been called with the expected calls when a key is missing
        self.assertEqual(mock_cc.call_args_list, expected)

    @httpretty.activate
    @patch('mcn.sm.so_manager.LOG.debug')
    def test_ensure_ssh_key_present(self, mock_log):
        # Initialization
        # mock GET key call
        httpretty.register_uri(httpretty.GET, "http://localhost:8888/public_key/",
                               status=200,
                               content_type='application/json',
                               adding_headers={
                                   'x-occi-location': '123456'
                               })

        # Test method
        #Check for key
        self.som._SOManager__ensure_ssh_key()

        # Asserts
        #Answer when key is present is a LOG entry
        mock_log.assert_called_with('Valid SM SSH is registered with OpenShift.')

    def test_extract_public_key_sanity(self):
        # Initialization
        ssh_key = 'ssh-rsa 123456 mykey'
        mock_op = mock_open(read_data=ssh_key)

        # Test method (with context manager mock_open)
        with patch('mcn.sm.so_manager.open', mock_op, create=True):
            resp = self.som._SOManager__extract_public_key()

        # Asserts
        self.assertEqual(resp, ('mykey', '123456'))

    def test_extract_public_key_dsa(self):
        # Initialization
        ssh_key = 'ssh-dsa 123456 mykey'
        mock_op = mock_open(read_data=ssh_key)

        # Test method (with context manager mock_open)
        with patch('mcn.sm.so_manager.open', mock_op, create=True):
            # Asserts exception
            self.assertRaises(Exception, self.som._SOManager__extract_public_key)

    @httpretty.activate
    def test_create_app(self):
        # Initialization
        # Tentative Kind/Resource Creation
        kind = Kind('http://schemas.mobile-cloud-networking.eu/occi/sm#',
                    'myservice',
                    title='Test Service',
                    attributes={'mcn.test.attribute1': 'immutable'},
                    related=[Resource.kind],
                    actions=[])
        entity = Resource('my-id', kind, None)
        httpretty.register_uri(httpretty.POST,
                               'http://localhost:8888/app/',
                               status=200,
                               content_type='application/json',
                               adding_headers={
                                   #why not x-occi-location ?
                                   'Location': 'http://localhost:8888/app/myservicelocation'
                               })
        httpretty.register_uri(httpretty.GET,
                               'http://localhost:8888/app/myservicelocation',
                               status=200,
                               content_type='text/occi',
                               adding_headers={
                                   'X-OCCI-Attribute':
                                       'occi.app.name="myse-srv-123", occi.app.repo="git@git.mcn.eu:myserv.git"'
                               })

        # Test method
        repo_uri = self.som._SOManager__create_app(entity, None)

        # Asserts
        self.assertEqual(repo_uri, 'git@git.mcn.eu:myserv.git')

    @patch('shutil.rmtree')
    @patch('shutil.copyfile')
    @patch('distutils.dir_util.copy_tree')
    @patch('tempfile.mkdtemp')
    @patch('os.system')
    def test_deploy_app(self, mock_os_system, mock_tempfile_mkdtemp, mock_dir_copy_tree, mock_copy_file, mock_rmtree):
        # Initialization
        repo = 'git@git.mcn.eu:myserv.git'
        tmp_dir = '/tmp/tempdir'
        mock_tempfile_mkdtemp.return_value = tmp_dir
        expected_os_system = [call(' '.join(['git', 'clone', repo, tmp_dir])),
                              call(' '.join(['chmod', '+x', os.path.join(tmp_dir, '.openshift', 'action_hooks', '*')])),
                              call(' '.join(['cd', tmp_dir, '&&', 'git', 'add', '-A'])),
                              call(' '.join(
                                  ['cd', tmp_dir, '&&', 'git', 'commit', '-m', '"deployment of SO for tenant X"',
                                   '-a'])),
                              call(' '.join(['cd', tmp_dir, '&&', 'git', 'push']))]
        expected_copy_file = [
            call('so/bundle/support/build', os.path.join(tmp_dir, '.openshift', 'action_hooks', 'build')),
            call('so/bundle/support/pre_start_python',
                 os.path.join(tmp_dir, '.openshift', 'action_hooks', 'pre_start_python')), ]

        # Test method
        self.som._SOManager__deploy_app(repo)

        # Asserts
        mock_tempfile_mkdtemp.assert_called_once()
        mock_dir_copy_tree.assert_called_with('so/bundle', tmp_dir)
        mock_rmtree.assert_called_with(tmp_dir)
        # Check if the CC mock has been called with the expected calls when a key is missing
        self.assertEqual(mock_os_system.call_args_list, expected_os_system)
        self.assertEqual(mock_copy_file.call_args_list, expected_copy_file)

    @httpretty.activate
    def test_init_so(self):
        # initialization
        kind = Kind('http://schemas.mobile-cloud-networking.eu/occi/sm#',
                    'myservice',
                    title='Test Service',
                    attributes={'mcn.test.attribute1': 'immutable'},
                    related=[Resource.kind],
                    actions=[])
        entity = Resource('my-id', kind, None)
        entity.extras = {}
        host = 'localhost:8888/myservice'
        entity.extras['host'] = host
        extras = {}
        extras['token'] = 'test_token'
        extras['tenant_name'] = 'test_tenantname'
        httpretty.register_uri(httpretty.POST,
                               'http://' + host + '/action=init',
                               status=200,
                               content_type='text/occi')

        # Test method
        self.som._SOManager__init_so(entity, extras)

        # Asserts
        sent_headers = httpretty.last_request().headers
        self.assertEqual(sent_headers['X-Auth-Token'], 'test_token')
        self.assertEqual(sent_headers['X-Tenant-Name'], 'test_tenantname')

    @httpretty.activate
    def test_deploy_so_sanity(self):
        # initialization
        kind = Kind('http://schemas.mobile-cloud-networking.eu/occi/sm#',
                    'myservice',
                    title='Test Service',
                    attributes={'mcn.test.attribute1': 'immutable'},
                    related=[Resource.kind],
                    actions=[])
        entity = Resource('my-id', kind, None)
        entity.extras = {}
        host = 'test.mcn.org:8888/myservice'
        entity.extras['host'] = host
        extras = {}
        extras['token'] = 'test_token'
        extras['tenant_name'] = 'test_tenantname'
        body_content = '123456789'
        httpretty.register_uri(httpretty.POST,
                               'http://' + host + '/action=deploy',
                               status=200,
                               body=body_content,
                               content_type='text/occi')

        # Test method
        self.som._SOManager__deploy_so(entity, extras)

        # Asserts
        self.assertEqual(entity.extras['stack_id'], body_content)

    @httpretty.activate
    def test_deploy_so_failure(self):
        # Initialization
        kind = Kind('http://schemas.mobile-cloud-networking.eu/occi/sm#',
                    'myservice',
                    title='Test Service',
                    attributes={'mcn.test.attribute1': 'immutable'},
                    related=[Resource.kind],
                    actions=[])
        entity = Resource('my-id', kind, None)
        entity.extras = {}
        host = 'test.mcn.org:8888/myservice'
        entity.extras['host'] = host
        extras = {}
        extras['token'] = 'test_token'
        extras['tenant_name'] = 'test_tenantname'
        body_content = 'Please initialize SO with token and tenant first.'
        httpretty.register_uri(httpretty.POST,
                               'http://' + host + '/action=deploy',
                               status=200,
                               body=body_content,
                               content_type='text/occi')

        # Test method and Assert exception
        self.assertRaises(Exception, self.som._SOManager__deploy_so, (entity, extras))


    @patch('mcn.sm.LOG')
    @patch('mcn.sm.so_manager.SOManager._SOManager__ensure_ssh_key')
    @patch('mcn.sm.so_manager.SOManager._SOManager__create_app')
    @patch('mcn.sm.so_manager.SOManager._SOManager__deploy_app')
    @patch('mcn.sm.so_manager.SOManager._SOManager__init_so')
    @patch('mcn.sm.so_manager.SOManager._SOManager__deploy_so')
    def test_deploy(self, mock_deploy_so, mock_init_so, mock_deploy_app, mock_create_app, mock_ensure_ssh, mcn_log):
        # Initialization
        kind = Kind('http://schemas.mobile-cloud-networking.eu/occi/sm#',
                    'myservice',
                    title='Test Service',
                    attributes={'mcn.test.attribute1': 'immutable'},
                    related=[Resource.kind],
                    actions=[])
        entity = Resource('my-id', kind, None)

        # repo uri is weird
        repo = 'http://git@git.mcn.eu:myserv.git'
        mock_create_app.return_value = repo

        # Test method
        self.som.deploy(entity, extras={})

        # Asserts
        mock_deploy_app.assert_called_with(repo)
        self.assertEqual(entity.extras['host'], 'git.mcn.eu:myserv.git')


    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_log.stop()
        self.patcher_system.stop()
        self.patcher_config_get.stop()


if __name__ == '__main__':
    unittest.main()
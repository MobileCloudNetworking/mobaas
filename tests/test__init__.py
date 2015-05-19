__author__ = 'florian'
import unittest, nose, os
from mock import patch, call, mock_open
import httpretty
from occi.core_model import Kind
from occi.core_model import Resource


if 'SM_CONFIG_PATH' not in os.environ:
    raise AttributeError('Please provide SM_CONFIG_PATH as env var.')

from sm.sm import config_logger
from sm.sm import get_params


class TestInitFunctions(unittest.TestCase):

    def setUp(self):
        pass

    @patch('mcn.sm.OptionParser')
    def config_logger_for_sanity(self, mock_opt):
        get_params()
        mock_opt.assert_called_once_with()

    @patch('mcn.sm.logging')
    def get_config_file_for_sanity(self, mock_logging):
        config_logger()
        mock_logging.assert_called_once_with()
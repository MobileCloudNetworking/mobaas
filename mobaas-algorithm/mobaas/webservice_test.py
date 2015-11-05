import unittest
from unittest import mock
#from unittest.mock import Mock, patch

from main import func


class FuncTestCase(unittest.TestCase):
    @mock.patch('main.urlopen')
    def test_func(self, mock_open):
        mock_open.return_value = '127.0.0.1'
        result = func()
        mock_open.assert_called_with('http://130.92.70.160/5000')
        self.assertEqual(result, '127.0.0.1')


if __name__ == '__main__':
    unittest.main()

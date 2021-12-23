from unittest import (
    TestCase,
    mock
)

from backupGD import credentials

CLIENT_SECRET_FOR_TEST = 'tests/client_secret.json'

class Test_get_credentials(TestCase):
    credentials = credentials.Credentials('token')


    @mock.patch('google_auth_oauthlib.flow.InstalledAppFlow.run_console')
    def test_no_args(self, run_console_mock: mock.Mock) -> None:
        run_console_mock.return_value = self.credentials
        actual = credentials.get_credentials()
        expect = self.credentials
        self.assertEqual(actual, expect)
        run_console_mock.assert_called_once()

    
    @mock.patch('google_auth_oauthlib.flow.InstalledAppFlow.run_console')
    def test_client_secret(self, run_console_mock: mock.Mock) -> None:
        run_console_mock.return_value = self.credentials
        actual = credentials.get_credentials(client_secret=CLIENT_SECRET_FOR_TEST)
        expect = self.credentials
        self.assertEqual(actual, expect)
        run_console_mock.assert_called_once()

    
    def test_unexist_client_secret(self) -> None:
        with self.assertRaises(FileNotFoundError):
            credentials.get_credentials(client_secret='unexist_client_secret.json')

    
    @mock.patch('google_auth_oauthlib.flow.InstalledAppFlow.run_local_server')
    def test_run_local_server(self, run_local_server_mock: mock.Mock) -> None:
        run_local_server_mock.return_value = self.credentials
        actual = credentials.get_credentials(use_local_server=True)
        expect = self.credentials
        self.assertEqual(actual, expect)
        run_local_server_mock.assert_called_once()
    

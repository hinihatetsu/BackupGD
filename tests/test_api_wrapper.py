from unittest import (
    TestCase,
    mock
)
import os
from pathlib import Path

from google.auth import exceptions as googleauthexceptions
from googleapiclient import (
    discovery,
    errors as googleapierrors
)

from backupGD import (
    api_wapper,
    credentials,
    exceptions
)

CLIENT_SECRET_FOR_TEST = 'tests/client_secret.json'
TOKEN_FOR_TEST = 'tests/token.json'
DUMMY_TAR = 'tests/dummy.tar.gz'
CREDENTIALS = credentials.Credentials.from_authorized_user_file(TOKEN_FOR_TEST) \
if os.path.exists(TOKEN_FOR_TEST) else credentials.get_credentials(CLIENT_SECRET_FOR_TEST)


def setUpModule() -> None:
    Path(DUMMY_TAR).touch()


def tearDownModule() -> None:
    Path(DUMMY_TAR).unlink()
    with open(TOKEN_FOR_TEST, 'w') as f:
        f.write(CREDENTIALS.to_json())


class Test_drive(TestCase):
    credentials = credentials.Credentials('token')

    @mock.patch('google_auth_oauthlib.flow.InstalledAppFlow.run_console')
    def test_no_args(self, run_console_mock: mock.Mock) -> None:
        run_console_mock.return_value = self.credentials
        with api_wapper.drive() as drive:
            self.assertEqual(drive._credentials, self.credentials)
        run_console_mock.assert_called_once()

    
    @mock.patch('google_auth_oauthlib.flow.InstalledAppFlow.run_console')
    def test_client_secret(self, run_console_mock: mock.Mock) -> None:
        run_console_mock.return_value = self.credentials
        with api_wapper.drive(CLIENT_SECRET_FOR_TEST) as drive:
            self.assertEqual(drive._credentials, self.credentials)
        run_console_mock.assert_called_once()



class TestGoogleDriveAPI___init__(TestCase):

    def test_valid_credentials(self) -> None:
        try:
            drive = api_wapper.GoogleDriveAPI(CREDENTIALS)
        except Exception as err:
            self.fail(f'{type(err)} is raised.')
        self.assertEqual(drive._credentials, CREDENTIALS)


    @mock.patch('google.oauth2.credentials.Credentials.valid', new_callable=mock.PropertyMock)
    @mock.patch('google.oauth2.credentials.Credentials.refresh')
    def test_refresh_failed(
        self, 
        credentials_refresh_mock: mock.Mock,
        credentials_valid_mock: mock.Mock
    ) -> None:
        credentials_refresh_mock.side_effect = Exception()
        credentials_valid_mock.return_value = False
        with self.assertRaises(ValueError):
            api_wapper.GoogleDriveAPI(CREDENTIALS)
        credentials_refresh_mock.assert_called_once()
        credentials_valid_mock.assert_called_once()


class TestGoogleDriveAPI_refresh(TestCase):

    @mock.patch('backupGD.credentials.Credentials.refresh')
    def test_default(self, credentials_refresh_mock: mock.Mock) -> None:
        credentials_refresh_mock.return_value = None
        drive = api_wapper.GoogleDriveAPI(CREDENTIALS)
        drive.refresh()
        credentials_refresh_mock.assert_called_once()

    
    @mock.patch('backupGD.credentials.Credentials.refresh')
    def test_refresh_error(self, credentials_refresh_mock: mock.Mock) -> None:
        credentials_refresh_mock.side_effect = googleauthexceptions.RefreshError()
        drive = api_wapper.GoogleDriveAPI(CREDENTIALS)
        with self.assertRaises(exceptions.RefreshError):
            drive.refresh()
        credentials_refresh_mock.assert_called_once()

    
    
class TestGoogleDriveAPI_get_folder_id(TestCase):

    def test_exist_folder(self) -> None:
        folder: str = 'backupGD-test'
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            expect = drive.create_folder(folder)
            actual = drive.get_folder_id(folder)
        self.assertEqual(actual, expect)
        clean_up([expect])
            
        
    def test_unexist_folder(self) -> None:
        folder = 'backupGD-test-unexist'
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            self.assertIsNone(drive.get_folder_id(folder))


    def test_API_call_failure(self) -> None:
        folder = 'backupGD-test'
        drive_mock = mock.Mock()
        drive_mock.files.side_effect = googleapierrors.HttpError(
            resp=mock.Mock(), content=b''
        )
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            drive._drive = drive_mock
            with self.assertRaises(exceptions.GoogleDriveAPIError):
                drive.get_folder_id(folder)




class TestGoogleDriveAPI_create_folder(TestCase):
    file_ids_to_delete: list[str] = []


    def setUp(self) -> None:
        self.file_ids_to_delete.clear()

    
    def tearDown(self) -> None:
        clean_up(self.file_ids_to_delete)


    def assertIsCreated(self, file_id: str) -> None:
        with discovery.build('drive', 'v3', credentials=CREDENTIALS) as drive:
            try:
                drive.files().get(fileId=file_id, fields='id').execute()
            except googleapierrors.HttpError as err:
                if err.status_code == 404:
                    self.fail(f'{file_id} is not created to GoogleDrive.')
                else:
                    raise


    def test_default(self) -> None:
        folder = 'backupGD-test'
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            folder_id = drive.create_folder(folder)
        self.file_ids_to_delete.append(folder_id)
        self.assertIsCreated(folder_id)


    def test_parent(self) -> None:
        parent = 'backupGD-test-parent'
        child = 'backupGD-test-child'
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            parent_id = drive.create_folder(folder_name=parent)
            folder_id = drive.create_folder(
                folder_name=child, 
                folder_id=parent_id
            )
        self.file_ids_to_delete.append(folder_id)
        self.file_ids_to_delete.append(parent_id)
        self.assertIsCreated(folder_id)


    def test_unexist_parent(self) -> None:
        folder = 'backupGD-test'
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            with self.assertRaises(exceptions.GoogleDriveAPIError):
                drive.create_folder(folder, 'backupGD-test-unexist')

    
    def test_API_call_failure(self) -> None:
        folder = 'backupGD-test'
        drive_mock = mock.Mock()
        drive_mock.files.side_effect = googleapierrors.HttpError(
            resp=mock.Mock(), content=b''
        )
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            drive._drive = drive_mock
            with self.assertRaises(exceptions.GoogleDriveAPIError):
                drive.create_folder(folder)



class TestGoogleDriveAPI_upload_backup(TestCase):
    folders: list[str] = [
        'backupGD-test-parent',
        'backupGD-test-child'
    ]
    file_ids_to_delete: list[str] = []


    def setUp(self) -> None:
        self.file_ids_to_delete.clear()


    def tearDown(self) -> None:
        clean_up(self.file_ids_to_delete)


    def assertIsUploaded(self, file_id: str) -> None:
        with discovery.build('drive', 'v3', credentials=CREDENTIALS) as drive:
            try:
                drive.files().get(fileId=file_id, fields='id').execute()
            except googleapierrors.HttpError as err:
                if err.status_code == 404:
                    self.fail(f'{file_id} is not uploaded to GoogleDrive.')
                else:
                    raise
            
            

    def test_default(self) -> None:
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            file_id = drive.upload_backup(DUMMY_TAR)
        self.file_ids_to_delete.append(file_id)
        self.assertIsUploaded(file_id)
            
    
    def test_parent(self) -> None:
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            folder_id: str = drive.create_folder(self.folders[0])
            file_id = drive.upload_backup(DUMMY_TAR, folder_id=folder_id)
        self.file_ids_to_delete.append(folder_id)
        self.file_ids_to_delete.append(file_id)
        self.assertIsUploaded(file_id)    
        

        
    def test_uexist_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
                drive.upload_backup('tests/unexists.tar.gz')

    
    def test_API_call_failure(self) -> None:
        drive_mock = mock.Mock()
        drive_mock.files.side_effect = googleapierrors.HttpError(
            resp=mock.Mock(), content=b''
        )
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            drive._drive = drive_mock
            with self.assertRaises(exceptions.GoogleDriveAPIError):
                drive.upload_backup(DUMMY_TAR)


class TestGoogleDriveAPI_delete_file(TestCase):

    def assertIsNotInGoogleDrive(self, file_id: str) -> None:
        with discovery.build('drive', 'v3', credentials=CREDENTIALS) as drive:
            with self.assertRaises(googleapierrors.HttpError):
                drive.files().get(fileId=file_id, fields='id').execute()


    def test_default(self) -> None:
        folder = 'backupGD-test'
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            folder_id: str = drive.create_folder(folder)
            drive.delete_file(folder_id)
        self.assertIsNotInGoogleDrive(folder_id)
    

    def test_API_call_failure(self) -> None:
        drive_mock = mock.Mock()
        drive_mock.files.side_effect = googleapierrors.HttpError(
            resp=mock.Mock(), content=b''
        )
        with api_wapper.GoogleDriveAPI(CREDENTIALS) as drive:
            drive._drive = drive_mock
            with self.assertRaises(exceptions.GoogleDriveAPIError):
                drive.delete_file('file_id')



def clean_up(file_ids_to_delete: list[str]) -> None:
    with discovery.build('drive', 'v3', credentials=CREDENTIALS) as drive:
        def delete(file_id: str) -> None:
            try:
                drive.files().delete(fileId=file_id).execute()
            except Exception:
                print(f'{file_id} could not be deleted.')
        list(map(delete, file_ids_to_delete))




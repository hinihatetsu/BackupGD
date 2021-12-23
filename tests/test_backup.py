from unittest import TestCase
import os

from backupGD import backup
DUMMY_DIRECTORY = 'tests/dummy'


def setUpModule() -> None:
    os.makedirs(DUMMY_DIRECTORY, exist_ok=True)


def tearDownModule() -> None:
    os.rmdir(DUMMY_DIRECTORY)


class Test_create_backup(TestCase):
    file_to_delete: list[str] = []

    def setUp(self) -> None:
        self.file_to_delete.clear()

    
    def tearDown(self) -> None:
        list(map(os.unlink, self.file_to_delete))


    def test_default(self) -> None:
        saved_path = backup.create_backup(DUMMY_DIRECTORY)
        self.assertTrue(os.path.exists(saved_path))
        if os.path.exists(saved_path):
            self.file_to_delete.append(saved_path)


    def test_dir(self) -> None:
        saved_path = backup.create_backup(DUMMY_DIRECTORY, dir='tests')
        self.assertTrue(os.path.exists(saved_path))
        if os.path.exists(saved_path):
            self.file_to_delete.append(saved_path)


    def test_unexist(self) -> None:
        with self.assertRaises(FileNotFoundError):
            backup.create_backup('tests/unexists')

    
    def test_unexist_dir(self) -> None:
        with self.assertRaises(FileNotFoundError):
            backup.create_backup(DUMMY_DIRECTORY, dir='unexist')
        
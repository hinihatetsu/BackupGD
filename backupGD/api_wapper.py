from __future__ import annotations
import os
import contextlib
from typing import Any, Union, Optional, Iterator

from googleapiclient import (
    discovery,
    errors as googleapierrors
)
from google.auth.transport import requests
from google.auth import exceptions as googleauthexceptions

from backupGD import (
    credentials,
    exceptions
)


class GoogleDriveAPI:
    """ GoogleDrive API Wrapper.
    
    Examples
    --------
    >>> import backupGD
    >>> credentials = backupGD.get_credentials()
    >>> with backupGD.GoogleDriveAPI(credentials) as drive:
    ...     drive.create_folder('backupGD')
    """
    _credentials: credentials.Credentials
    _drive: Any


    def __init__(self, credentials: credentials.Credentials) -> None:
        """ 
        Parameters
        ----------
        credentials : backupGD.credentials.Credentials
            Credentials for Google API.

        Raises
        ------
        ValueError
            If credentials is invalid.

        """
        self._credentials = credentials
        if not credentials.valid:
            try:
                self.refresh()
            except Exception as err:
                raise ValueError(
                    '''
                    "credentials" argument is invalid.
                    Get new one by calling `backupGD.get_credentials()`.
                    '''
                ) from err
        

    def __enter__(self) -> GoogleDriveAPI:
        self._drive = discovery.build(
            'drive', 
            'v3', 
            credentials=self._credentials,
            cache_discovery=False
        )
        return self


    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self._drive.close()


    def refresh(self) -> None:
        """ Refresh credentials. 
        
        Raises
        ------
        backupGD.exceptions.RefreshError
            If the credentials could not be refreshed.
        """
        with requests.requests.session() as session:
            try:
                self._credentials.refresh(requests.Request(session))
            except googleauthexceptions.RefreshError as err:
                raise exceptions.RefreshError(err)


    def create_folder(
        self,
        folder_name: str,
        folder_id: Optional[str] = None
    ) -> str:
        """ Create folder on GoogleDrive

        Parameters
        ----------
        folder_name : str
            Folder name on GoogleDrive.
        folder_id : str | None
            Parent folder ID on GoogleDrive.

        Returns
        -------
        str
            ID of created folder.

        Raises
        ------
        backupGD.exceptions.GoogleDriveAPIError
            If GoogleDrive API call failed.
        """
        if folder_id:
            parents: list[str] = [folder_id]
        else:
            parents = []
        file_metadata: dict[str, Any] = {
            'name': str(folder_name),
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': parents
        }
        try:
            response = self._drive.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
        except googleapierrors.HttpError as err:
            raise exceptions.GoogleDriveAPIError(
                err.status_code, 
                err._get_reason()
            ) from err
        return str(response.get('id'))


    def get_folder_id(self, folder_name: str) -> Optional[str]:
        """ Get folder ID on GoogleDrive. 
        
        Parameters
        ----------
        folder_name : str
            Folder name on GoogleDrive.

        Returns
        -------
        str | None
            Folder ID if exists else None.

        Raises
        ------
        backupGD.exceptions.GoogleDriveAPIError
            If GoogleDrive API call failed.
        """
        folder_name = str(folder_name)
        page_token = None
        while True:
            try:
                response = self._drive.files().list(
                    q='mimeType="application/vnd.google-apps.folder"',
                    fields='nextPageToken, files(id, name)',
                    pageToken=page_token
                ).execute()
            except googleapierrors.HttpError as err:
                raise exceptions.GoogleDriveAPIError(
                    err.status_code, 
                    err._get_reason()
                ) from err
            for file in response.get('files', []):
                if file.get('name') == folder_name:
                    return str(file.get('id'))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return None


    def upload_backup(
        self,
        tarfile: Union[str, os.PathLike[str]], *, 
        folder_id: Optional[str] = None
    ) -> str:
        """ Upload a gzipped tar file to GoogleDrive. 
        
        Parameters
        ----------
        tarfile : str | os.Pathlike[str]
            Path to gzipped tar file to upload.
        folder_id : str | None
            Folder ID of GoogleDrive.
        
        Returns
        -------
        str
            File ID of uploaded file.

        Raises
        ------
        FileNotFoundError
            If "tarfile" could not be found.
        backupGD.exceptions.GoogleDriveAPIError
            If GoogleDrive API call failed.
        """
        if not os.path.exists(tarfile):
            raise FileNotFoundError(
                f'tar file `{tarfile}` not found.'
            )
        if folder_id:
            parents: list[str] = [folder_id]
        else:
            parents = []
        file_metadata = {
            'name': tarfile,
            'mimeType': 'application/gzip',
            'parents': parents
        }
        media = discovery.MediaFileUpload(
            tarfile, 
            mimetype='application/gzip',
        )
        try:
            response = self._drive.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
        except googleapierrors.HttpError as err:
            raise exceptions.GoogleDriveAPIError(
                err.status_code, 
                err._get_reason()
            ) from err
        return str(response.get('id'))

    
    def delete_file(self, file_id: str) -> None:
        """ Delete file on GoogleDrive.
        
        Parameters
        ----------
        file_id : str
            File ID to delete.
        
        Raises
        ------
        backupGD.exceptions.GoogleDriveAPIError
            If GoogleDrive API call failed.
        """
        try:
            self._drive.files().delete(fileId=file_id).execute()
        except googleapierrors.HttpError as err:
            raise exceptions.GoogleDriveAPIError(
                err.status_code, 
                err._get_reason()
            ) from err
            


@contextlib.contextmanager
def drive(client_secret: Union[str, os.PathLike[str], None] = None) -> Iterator[GoogleDriveAPI]:
    """ High Level API for GoogleDriveAPI.

    Parameters
    ----------
    client_secret : str | os.PathLike[str] | None
        Path to client secret json file.

    Yields
    ------
    GoogleDriveAPI
        
    Examples
    --------
    >>> import backupGD
    >>> backup = backupGD.create_backup('.')
    >>> with backupGD.drive() as drive:
    ...     drive.upload_backup(backup)

    """
    creds = credentials.get_credentials(client_secret)
    with GoogleDriveAPI(creds) as drive:
        yield drive

    
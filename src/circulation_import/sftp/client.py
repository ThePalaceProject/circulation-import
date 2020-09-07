from __future__ import annotations

import logging
import os
from types import TracebackType
from typing import List
from typing import Optional
from typing import Type

import paramiko
from paramiko import Transport

from circulation_import.sftp.configuration import SFTPConfiguration


class SFTPClient:
    def __init__(self, configuration: SFTPConfiguration) -> None:
        self._configuration: SFTPConfiguration = configuration
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._transport: Optional[Transport] = None
        self._client_instance: Optional[paramiko.SFTPClient] = None

    def __enter__(self) -> SFTPClient:
        return self

    def __exit__(
            self,
            exception_type: Type[BaseException],
            exception_instance: BaseException,
            exception_traceback: TracebackType) -> None:
        if self._client_instance:
            self._logger.debug('Started closing SFTP session and its underlying channel')

            self._client_instance.close()

            self._logger.debug('Finished closing SFTP session and its underlying channel')
        if self._transport:
            self._logger.debug('Started closing the transport session')

            self._transport.close()

            self._logger.debug('Finished closing the transport session')

    @property
    def _client(self) -> paramiko.SFTPClient:
        if self._client_instance is None:
            self._logger.debug('Started creating a new SFTP client')

            self._logger.debug('Started creating a new transport instance')
            self._transport = paramiko.Transport((self._configuration.host, self._configuration.port))

            self._logger.debug('Starting a new SSH session')
            self._transport.connect(None, self._configuration.username, self._configuration.password)

            self._client_instance = paramiko.SFTPClient.from_transport(self._transport)

            self._logger.debug('Finished creating a new SFTP client')

        return self._client_instance

    def upload(self, local_file_path: str, remote_file_path: Optional[str] = None) -> None:
        self._logger.debug(f'Started uploading local file {local_file_path} to {remote_file_path}')

        if not remote_file_path:
            file_name = os.path.basename(local_file_path)
            remote_file_path = os.path.join(self._configuration.upload_directory, file_name)

            self._logger.debug(f'There is no remote file path specified. New file remote file path: {remote_file_path}')

        self._client.put(local_file_path, remote_file_path)

        self._logger.debug(f'Finished uploading local file {local_file_path} to {remote_file_path}')

    def download(self, remote_file_path: str, local_file_path: str) -> None:
        self._logger.debug(f'Started downloading {remote_file_path} to {local_file_path}')

        self._client.get(remote_file_path, local_file_path)

        self._logger.debug(f'Finished downloading {remote_file_path} to {local_file_path}')

    def remove(self, remote_file_path: str) -> None:
        self._logger.debug(f'Started removing {remote_file_path}')

        self._client.remove(remote_file_path)

        self._logger.debug(f'Finished removing {remote_file_path}')

    def mkdir(self, remote_path: str) -> None:
        self._logger.debug(f'Started creating {remote_path} directory')

        self._client.mkdir(remote_path)

        self._logger.debug(f'Finished creating {remote_path} directory')

    def list_dir(self, remote_path: str) -> List[str]:
        self._logger.debug(f'Started listing directory {remote_path}')

        files = self._client.listdir(remote_path)

        self._logger.debug(f'Finished listing directory {remote_path}')

        return files

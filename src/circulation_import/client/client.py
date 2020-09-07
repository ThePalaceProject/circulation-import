import datetime
import logging
import os
import tempfile
import time
from typing import List
from typing import Tuple

from circulation_import import utils
from circulation_import.client.configuration import ClientConfiguration
from circulation_import.client.configuration import CollectionConfiguration
from circulation_import.metadata.configuration import BookImportMetadata
from circulation_import.metadata.configuration import CollectionImportMetadata
from circulation_import.metadata.configuration import Directory
from circulation_import.metadata.configuration import MetadataFile
from circulation_import.metadata.serialization import CollectionImportMetadataSerializer
from circulation_import.sftp.client import SFTPClient
from circulation_import.storage.model import ProcessingStatus


class Client:
    def __init__(
            self,
            configuration: ClientConfiguration,
            sftp_client: SFTPClient,
            report_serializer: CollectionImportMetadataSerializer) -> None:
        self._configuration: ClientConfiguration = configuration
        self._sftp_client: SFTPClient = sftp_client
        self._report_serializer: CollectionImportMetadataSerializer = report_serializer
        self._logger: logging.Logger = logging.getLogger(__name__)

    def _create_remote_directory(self, remote_directory: str) -> None:
        self._logger.debug(f'Started creating {remote_directory}')

        base_directory = os.path.dirname(remote_directory)

        if base_directory:
            self._create_remote_directory(base_directory)

        try:
            self._sftp_client.list_dir(remote_directory)

            self._logger.debug(f'{remote_directory} already exists, skipping')

            # If the directory already exists, we don't need to do anything
        except Exception:
            self._logger.debug(f'{remote_directory} does not exist, creating it')

            # If we cannot list the directory, it probably means that it doesn't exist
            self._sftp_client.mkdir(remote_directory)

        self._logger.debug(f'Finished creating {remote_directory}')

    @staticmethod
    def _has_extension(file_name: str, extensions: List[str]) -> bool:
        file_extension = os.path.splitext(file_name)[1]

        return file_extension in extensions

    def _upload_books(
            self, local_books_directory: str, remote_books_directory: str) -> List[BookImportMetadata]:
        self._logger.info(f'Started uploading books from {local_books_directory} to {remote_books_directory}')

        books_metadata = []

        for (directory, subdirectories, book_files) in os.walk(local_books_directory):
            for book_file in book_files:
                if not self._has_extension(book_file, self._configuration.book_file_types):
                    continue

                local_book_file_path = os.path.join(directory, book_file)
                book_metadata = BookImportMetadata(
                    name=book_file,
                    hash=utils.calculate_file_hash(local_book_file_path, self._configuration.hashing_algorithm)
                )

                books_metadata.append(book_metadata)

                remote_book_file_path = os.path.join(
                    remote_books_directory,
                    book_file
                )

                self._sftp_client.upload(local_book_file_path, remote_book_file_path)

            break

        self._logger.info(
            f'Finished uploading books from {local_books_directory} to {remote_books_directory}. '
            f'Finished {len(books_metadata)} books')

        return books_metadata

    def _upload_covers(self, local_covers_directory: str, remote_covers_directory: str) -> None:
        self._logger.info(f'Started uploading covers from {local_covers_directory} to {remote_covers_directory}')

        covers = 0

        for (directory, subdirectories, cover_files) in os.walk(local_covers_directory):
            for cover_file in cover_files:
                if not self._has_extension(cover_file, self._configuration.cover_file_types):
                    continue

                covers += 1

                local_cover_file_path = os.path.join(directory, cover_file)
                remote_cover_file_path = os.path.join(
                    remote_covers_directory,
                    cover_file
                )

                self._sftp_client.upload(local_cover_file_path, remote_cover_file_path)

            break

        self._logger.info(
            f'Finished uploading covers from {local_covers_directory} to {remote_covers_directory}. '
            f'Found {covers} covers')

    def _upload_metadata_file(self, local_metadata_file: str, remote_metadata_file: str) -> None:
        self._logger.info(f'Started uploading metadata file {local_metadata_file} to {remote_metadata_file}')

        self._sftp_client.upload(local_metadata_file, remote_metadata_file)

        self._logger.info(f'Finished uploading metadata file {local_metadata_file} to {remote_metadata_file}')

    def _upload_import_metadata_file(
            self, collection_import_metadata: CollectionImportMetadata, remote_import_metadata_file: str) -> None:
        self._logger.info(
            f'Started uploading import metadata file {MetadataFile.IMPORT_METADATA_FILE.value} '
            f'to {remote_import_metadata_file}')

        with tempfile.NamedTemporaryFile() as temporary_file:
            collection_import_metadata.save(temporary_file)
            temporary_file.flush()

            self._sftp_client.upload(temporary_file.name, remote_import_metadata_file)

        self._logger.info(
            f'Finished uploading import metadata file {MetadataFile.IMPORT_METADATA_FILE.value} '
            f'to {remote_import_metadata_file}')

    def _download_report(self, remote_report_path: str) -> CollectionImportMetadata:
        self._logger.info(f'Started downloading {remote_report_path}')

        with tempfile.TemporaryDirectory() as temporary_directory:
            local_report_path = os.path.join(
                temporary_directory,
                MetadataFile.REPORT_FILE.value
            )

            self._sftp_client.download(remote_report_path, local_report_path)

            report = CollectionImportMetadata.load(local_report_path)

            self._logger.info(f'Finished downloading {remote_report_path}')

            return report

    def _save_report_locally(self, local_reports_directory: str, report: CollectionImportMetadata) -> str:
        self._logger.info(f'Started saving report to {local_reports_directory}')

        date_time_suffix = datetime.datetime.utcnow().strftime('_%Y-%m-%d_%H-%M-%S')
        public_report_path = os.path.join(
            local_reports_directory,
            'report'
        ) + date_time_suffix + self._report_serializer.extension

        self._report_serializer.serialize(report, public_report_path)

        self._logger.info(f'Finished saving report to {public_report_path}')

        return public_report_path

    def _wait_for_report(
            self,
            collection_configuration: CollectionConfiguration,
            remote_reports_directory: str) -> Tuple[CollectionImportMetadata, str]:
        self._logger.info(f'Started waiting for a report in {remote_reports_directory}')

        if not os.path.exists(collection_configuration.reports_directory):
            os.makedirs(collection_configuration.reports_directory)

        while True:
            time.sleep(self._configuration.polling_time_seconds)

            files = self._sftp_client.list_dir(remote_reports_directory)

            self._logger.info(f'Found the following files in {remote_reports_directory}: {files}')

            for file in files:
                if MetadataFile.REPORT_FILE.value in file:
                    remote_report_path = os.path.join(
                        remote_reports_directory,
                        MetadataFile.REPORT_FILE.value
                    )

                    report = self._download_report(remote_report_path)
                    public_report_path = self._save_report_locally(collection_configuration.reports_directory, report)
                    self._sftp_client.remove(remote_report_path)

                    self._logger.info(f'Report has been saved to {public_report_path}')

                    return report, public_report_path

    def _print_result(self, report: CollectionImportMetadata, public_report_path: str) -> None:
        failed = any([book.status == ProcessingStatus.FAILED.value for book in report.books])

        if failed:
            self._logger.error(f'Import failed. Please refer to {public_report_path} for more details')
        else:
            self._logger.info('Import succeeded')

    def run(self, collection_configuration: CollectionConfiguration) -> None:
        self._logger.info(
            f'Started importing a collection using the following configuration: {collection_configuration}')

        collection_directory = os.path.join(
            self._configuration.sftp_configuration.upload_directory,
            collection_configuration.collection_name,
            collection_configuration.data_source_name
        )

        remote_books_directory = os.path.join(
            collection_directory,
            Directory.BOOKS_DIRECTORY.value
        )
        self._create_remote_directory(remote_books_directory)

        remote_covers_directory = os.path.join(
            collection_directory,
            Directory.COVERS_DIRECTORY.value
        )
        self._create_remote_directory(remote_covers_directory)

        remote_reports_directory = os.path.join(
            collection_directory,
            Directory.REPORTS_DIRECTORY.value
        )
        self._create_remote_directory(remote_reports_directory)

        remote_metadata_file = os.path.join(
            collection_directory,
            MetadataFile.COLLECTION_METADATA_FILE.value
        )
        remote_import_metadata_file = os.path.join(
            collection_directory,
            MetadataFile.IMPORT_METADATA_FILE.value
        )

        books = self._upload_books(collection_configuration.books_directory, remote_books_directory)
        self._upload_covers(collection_configuration.covers_directory, remote_covers_directory)
        self._upload_metadata_file(collection_configuration.metadata_file, remote_metadata_file)

        collection_import_metadata = CollectionImportMetadata(
            collection_name=collection_configuration.collection_name,
            data_source_name=collection_configuration.data_source_name,
            timestamp=datetime.datetime.utcnow(),
            books_directory=remote_books_directory,
            covers_directory=remote_covers_directory,
            reports_directory=remote_reports_directory,
            metadata_file=remote_metadata_file,
            metadata_format=collection_configuration.metadata_format,
            books=books
        )
        self._upload_import_metadata_file(collection_import_metadata, remote_import_metadata_file)

        report, public_report_path = self._wait_for_report(collection_configuration, remote_reports_directory)

        self._print_result(report, public_report_path)

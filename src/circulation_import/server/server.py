import logging
import os
import threading
import time
from typing import Optional

from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from circulation_import import utils
from circulation_import.metadata.configuration import CollectionImportMetadata
from circulation_import.metadata.configuration import MetadataFile
from circulation_import.server.configuration import ServerConfiguration
from circulation_import.server.importer import Importer
from circulation_import.server.storage import ServerStorage
from circulation_import.storage.configuration import DatabaseDriver
from circulation_import.storage.model import BookMetadata
from circulation_import.storage.model import CollectionMetadata
from circulation_import.storage.model import ProcessingStatus


class Server:
    def __init__(self, configuration: ServerConfiguration, storage: ServerStorage, importer: Importer) -> None:
        self._configuration: ServerConfiguration = configuration
        self._storage: ServerStorage = storage
        self._importer: Importer = importer
        self._lock = threading.Lock()
        self._logger: logging.Logger = logging.getLogger(__name__)

    def _get_local_path(self, directory: str, file_name: Optional[str] = None) -> str:
        base_directory = os.path.normpath(self._configuration.upload_directory)
        common_directory = os.path.basename(base_directory)

        if common_directory in directory or (file_name and common_directory in file_name):
            base_directory = base_directory.rstrip(common_directory)

        local_path = os.path.join(
            base_directory,
            directory
        )

        if file_name:
            local_path = os.path.join(
                local_path,
                file_name
            )

        return local_path

    def _process_import_metadata(self, collection_import_metadata: CollectionImportMetadata) -> CollectionMetadata:
        self._logger.info(f'Started processing {collection_import_metadata}')

        collection_metadata = self._storage.find_collection(collection_import_metadata)

        if collection_metadata is not None:
            self._logger.info(f'Collection {collection_import_metadata} already exists: {collection_metadata}')
        else:
            self._logger.info(f'Collection {collection_import_metadata} does not exist, started creating a new one')

            local_books_directory = self._get_local_path(collection_import_metadata.books_directory)
            local_covers_directory = self._get_local_path(collection_import_metadata.covers_directory)
            local_reports_directory = self._get_local_path(collection_import_metadata.reports_directory)
            local_metadata_file = self._get_local_path('', collection_import_metadata.metadata_file)
            collection_metadata = CollectionMetadata(
                collection_name=collection_import_metadata.collection_name,
                data_source_name=collection_import_metadata.data_source_name,
                timestamp=collection_import_metadata.timestamp,
                books_directory=local_books_directory,
                covers_directory=local_covers_directory,
                reports_directory=local_reports_directory,
                metadata_file=local_metadata_file,
                metadata_format=collection_import_metadata.metadata_format
            )

            self._logger.info(f'Finished creating a new collection: {collection_metadata}')

        for book_import_metadata in collection_import_metadata.books:
            self._logger.debug(f'Started processing {book_import_metadata}')

            book_metadata = self._storage.find_book(collection_metadata, book_import_metadata)

            if book_metadata is not None:
                self._logger.debug(f'Book {book_import_metadata} already exists: {book_metadata}')
            else:
                self._logger.debug(f'Book {book_import_metadata} does not exist, started creating a new one')

                book_metadata = BookMetadata(
                    name=book_import_metadata.name,
                    _hash=book_import_metadata.hash,
                )

                collection_metadata.books.append(book_metadata)

                self._logger.debug(f'Finished creating a new book: {book_metadata}')

            if book_metadata.status not in [ProcessingStatus.PROCESSED.value, ProcessingStatus.FAILED.value]:
                local_book_file_path = self._get_local_path(
                    collection_import_metadata.books_directory, book_metadata.name)
                book_hash = utils.calculate_file_hash(local_book_file_path, self._configuration.hashing_algorithm)

                if book_hash != book_metadata.hash:
                    book_metadata.status = ProcessingStatus.FAILED.value
                    book_metadata.error = 'Hash does not match'

                    self._logger.error(f'Book {book_metadata} is corrupted')

            self._logger.debug(f'Finished processing {book_import_metadata}: {book_metadata}')

        self._logger.info(f'Finished processing {collection_import_metadata}: {collection_metadata}')

        return collection_metadata

    def _save_report(
            self,
            collection_import_metadata: CollectionImportMetadata,
            collection_metadata: CollectionMetadata) -> None:
        self._logger.info(f'Started saving report for {collection_metadata}')

        book_import_metadata_dictionary = {item.name: item for item in collection_import_metadata.books}

        for book_metadata in collection_metadata.books:
            book_import_metadata = book_import_metadata_dictionary[book_metadata.name]
            book_import_metadata.status = book_metadata.status
            book_import_metadata.error = book_metadata.error

        local_report_file_path = self._get_local_path(
            collection_import_metadata.reports_directory, MetadataFile.REPORT_FILE.value)

        collection_import_metadata.save(local_report_file_path)

        self._logger.info(f'Finished saving report for {collection_metadata} to {local_report_file_path}')

    def _import_collection(self, import_metadata_file: str) -> None:
        self._logger.info(f'Started importing the collection from {import_metadata_file}')

        # We have to use a critical section in the case of SQLite because it doesn't allow
        # multi-threaded access to the database
        if self._configuration.database_configuration.driver == DatabaseDriver.SQLITE.value:
            self._lock.acquire()

        try:
            collection_import_metadata = CollectionImportMetadata.load(import_metadata_file)

            collection_metadata = self._process_import_metadata(collection_import_metadata)
            self._storage.add(collection_metadata)
            self._storage.commit()

            self._importer.run(collection_metadata)
            self._storage.commit()

            self._save_report(collection_import_metadata, collection_metadata)
        except Exception:
            self._logger.exception('An unexpected exception occurred during during collection import')

            raise
        finally:
            if self._configuration.database_configuration.driver == DatabaseDriver.SQLITE.value:
                self._lock.release()

        self._logger.info(f'Finished importing the collection from {import_metadata_file}')

    def _process_file_system_event(self, event: FileSystemEvent) -> None:
        self._logger.debug(f'Received the following event: {event}')

        file_name = os.path.basename(event.src_path)

        if file_name == MetadataFile.IMPORT_METADATA_FILE.value:
            time.sleep(1)  # Wait 1 second to make sure that the file is available

            self._import_collection(event.src_path)

    def run(self) -> None:
        self._logger.info('Started running the server')

        event_handler = FileSystemEventHandler()
        event_handler.on_created = self._process_file_system_event
        event_handler.on_modified = self._process_file_system_event

        observer = Observer()
        observer.schedule(event_handler, self._configuration.upload_directory, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except Exception:
            self._logger.exception('An unexpected exception occurred during watching file changes')

            observer.stop()

        observer.join()

        self._logger.info('Finished running the server')

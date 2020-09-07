import logging
import shutil
import subprocess
import tempfile
from typing import List

from ruamel.yaml import os

from circulation_import.server.configuration import ImporterConfiguration
from circulation_import.storage.model import CollectionMetadata
from circulation_import.storage.model import ProcessingStatus


class Importer:
    def __init__(self, configuration: ImporterConfiguration) -> None:
        self._configuration: ImporterConfiguration = configuration
        self._logger = logging.getLogger(__name__)

    def _create_parameters(self, collection_metadata: CollectionMetadata, new_book_directory: str) -> List:
        parameters = [self._configuration.import_script_command]

        parameters.extend(
            [
                '--collection-name',
                self._configuration.collection_name,
                '--collection-type',
                self._configuration.collection_type,
                '--data-source-name',
                self._configuration.data_source_name,
                '--metadata-format',
                collection_metadata.metadata_format,
                '--metadata-file',
                collection_metadata.metadata_file,
                '--ebook-directory',
                new_book_directory,
                '--cover-directory',
                collection_metadata.covers_directory,
                '--rights-uri',
                self._configuration.rights_uri
            ]
        )

        return parameters

    def run(self, collection_metadata: CollectionMetadata) -> None:
        self._logger.info(f'Started importing {collection_metadata}')

        for book_metadata in collection_metadata.books:
            self._logger.debug(f'Started processing {book_metadata}')

            if book_metadata.status == ProcessingStatus.PROCESSED.value:
                self._logger.debug(f'Book {book_metadata} has been already processed, skipping')
                continue

            with tempfile.TemporaryDirectory() as temporary_directory:
                new_book_path = os.path.join(
                    temporary_directory,
                    book_metadata.name
                )
                shutil.copy(book_metadata.full_path, new_book_path)

                self._logger.debug(f'Copying {book_metadata.full_path} to {new_book_path}')

                parameters = self._create_parameters(collection_metadata, temporary_directory)

                self._logger.debug(f'directory_import\'s parameters: {parameters}')

                try:
                    output = subprocess.check_output(' '.join(parameters), shell=True, executable='/bin/bash')

                    self._logger.debug(f'Output of directory_import: {output}')

                    book_metadata.status = ProcessingStatus.PROCESSED.value
                    book_metadata.error = None

                    self._logger.debug(f'Finished processing {book_metadata}')
                except Exception:
                    self._logger.exception(
                        'An unexpected exception occurred during running the directory_import script')

                    book_metadata.status = ProcessingStatus.FAILED.value
                    book_metadata.error = 'bin/directory_import script failed'

        self._logger.info(f'Finished importing {collection_metadata}')

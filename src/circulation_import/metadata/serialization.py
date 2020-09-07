import csv
import logging
from abc import ABC
from abc import abstractmethod

from circulation_import.metadata.configuration import CollectionImportMetadata


class CollectionImportMetadataSerializer(ABC):
    @property
    def extension(self):
        raise NotImplementedError()

    @abstractmethod
    def serialize(self, collection_import_metadata: CollectionImportMetadata, file_path: str) -> None:
        raise NotImplementedError()


class CollectionImportMetadataCSVSerializer(CollectionImportMetadataSerializer):
    DEFAULT_DELIMITER: str = ','
    DEFAULT_QUOTE_CHAR: str = '"'

    def __init__(self, delimiter: str = DEFAULT_DELIMITER, quote_char: str = DEFAULT_QUOTE_CHAR) -> None:
        self._delimiter: str = delimiter
        self._quote_char: str = quote_char
        self._logger: logging.Logger = logging.getLogger(__name__)

    @property
    def extension(self):
        return '.csv'

    def serialize(self, collection_import_metadata: CollectionImportMetadata, file_path: str) -> None:
        self._logger.info(f'Started serializing {collection_import_metadata} to {file_path}')

        with open(file_path, 'w') as output_file:
            writer = csv.writer(output_file, delimiter=self._delimiter, quotechar=self._quote_char)

            writer.writerow(['Name', 'Hash', 'Status', 'Error'])

            for book in collection_import_metadata.books:
                self._logger.debug(f'Serializing item {book}')

                writer.writerow([book.name, book.hash, book.status, book.error])

        self._logger.info(f'Finished serializing {collection_import_metadata} to {file_path}')

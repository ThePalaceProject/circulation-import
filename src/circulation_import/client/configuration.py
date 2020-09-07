from typing import List

from attr import dataclass
from ruamel.yaml import yaml_object

from circulation_import.configuration import Configuration
from circulation_import.configuration import yaml
from circulation_import.hash import HashingAlgorithm
from circulation_import.sftp.configuration import SFTPConfiguration
from circulation_import.storage.model import MetadataFormat
from circulation_import.storage.storage import DatabaseConfiguration


@dataclass(kw_only=True)
@yaml_object(yaml)
class CollectionConfiguration:
    collection_name: str
    data_source_name: str
    books_directory: str
    covers_directory: str
    reports_directory: str
    metadata_file: str
    metadata_format: MetadataFormat

    def __repr__(self) -> str:
        return f'<CollectionConfiguration(' \
            f'collection_name={self.collection_name}, ' \
            f'data_source_name={self.data_source_name}, ' \
            f'books_directory={self.books_directory}, ' \
            f'covers_directory={self.covers_directory}, ' \
            f'reports_directory={self.reports_directory}, ' \
            f'metadata_file={self.metadata_file}, ' \
            f'metadata_format={self.metadata_format})>'


@dataclass(kw_only=True)
@yaml_object(yaml)
class ClientConfiguration(Configuration):
    DEFAULT_BOOK_FILE_TYPES = ['.pdf', '.epub']
    DEFAULT_COVER_FILE_TYPES = ['.png', '.jpeg']
    DEFAULT_POLLING_TIME_SECONDS = 10

    database_configuration: DatabaseConfiguration
    sftp_configuration: SFTPConfiguration
    hashing_algorithm: HashingAlgorithm
    book_file_types: List[str] = DEFAULT_BOOK_FILE_TYPES
    cover_file_types: List[str] = DEFAULT_COVER_FILE_TYPES
    polling_time_seconds: int = DEFAULT_POLLING_TIME_SECONDS

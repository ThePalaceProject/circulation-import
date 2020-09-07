import datetime
from enum import Enum
from typing import List
from typing import Optional

from attr import dataclass
from ruamel.yaml import yaml_object

from circulation_import.configuration import Configuration
from circulation_import.configuration import yaml
from circulation_import.storage.model import MetadataFormat
from circulation_import.storage.model import ProcessingStatus


@dataclass(kw_only=True)
@yaml_object(yaml)
class BookImportMetadata(Configuration):
    name: str
    hash: str
    status: ProcessingStatus = ProcessingStatus.NEW.value
    error: Optional[str] = None


@dataclass(kw_only=True)
@yaml_object(yaml)
class CollectionImportMetadata(Configuration):
    collection_name: str
    data_source_name: str
    timestamp: datetime.datetime
    books_directory: str
    covers_directory: str
    reports_directory: str
    metadata_file: str
    metadata_format: MetadataFormat
    books: List[BookImportMetadata]


class Directory(Enum):
    BOOKS_DIRECTORY = 'books'
    COVERS_DIRECTORY = 'covers'
    REPORTS_DIRECTORY = 'reports'


class MetadataFile(Enum):
    COLLECTION_METADATA_FILE = 'metadata.xml'
    IMPORT_METADATA_FILE = 'import-metadata.yml'
    REPORT_FILE = 'report.yml'

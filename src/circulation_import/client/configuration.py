from typing import List

from attr import dataclass
from ruamel.yaml import yaml_object

from circulation_import.configuration import Configuration
from circulation_import.configuration import yaml
from circulation_import.hash import HashingAlgorithm
from circulation_import.sftp.configuration import SFTPConfiguration
from circulation_import.storage.storage import DatabaseConfiguration


@dataclass(kw_only=True)
@yaml_object(yaml)
class ClientConfiguration(Configuration):
    DEFAULT_BOOK_FILE_TYPES = [".pdf", ".epub"]
    DEFAULT_COVER_FILE_TYPES = [".png", ".jpg", ".jpeg"]
    DEFAULT_POLLING_TIME_SECONDS = 10

    database_configuration: DatabaseConfiguration
    sftp_configuration: SFTPConfiguration
    hashing_algorithm: HashingAlgorithm
    book_file_types: List[str] = DEFAULT_BOOK_FILE_TYPES
    cover_file_types: List[str] = DEFAULT_COVER_FILE_TYPES
    polling_time_seconds: int = DEFAULT_POLLING_TIME_SECONDS
    import_content: bool = True

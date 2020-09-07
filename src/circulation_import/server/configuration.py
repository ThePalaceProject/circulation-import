from enum import Enum

from attr import dataclass
from ruamel.yaml import yaml_object

from circulation_import.configuration import Configuration
from circulation_import.configuration import yaml
from circulation_import.hash import HashingAlgorithm
from circulation_import.storage.storage import DatabaseConfiguration


class CollectionType(Enum):
    OPEN_ACCESS = 'OPEN_ACCESS'
    PROTECTED_ACCESS = 'PROTECTED_ACCESS'
    LCP = 'LCP'

    def __str__(self) -> str:
        return str(self.name)


@dataclass(kw_only=True)
@yaml_object(yaml)
class ImporterConfiguration(Configuration):
    import_script_command: str = 'bin/directory_import'
    collection_name: str
    collection_type: CollectionType
    data_source_name: str
    rights_uri: str = 'http://librarysimplified.org/terms/rights-status'


@dataclass(kw_only=True)
@yaml_object(yaml)
class ServerConfiguration(Configuration):
    database_configuration: DatabaseConfiguration
    importer_configuration: ImporterConfiguration
    hashing_algorithm: HashingAlgorithm
    upload_directory: str

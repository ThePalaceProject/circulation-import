from attr import dataclass
from ruamel.yaml import yaml_object

from circulation_import.configuration import yaml


@dataclass(kw_only=True)
@yaml_object(yaml)
class SFTPConfiguration:
    host: str
    port: str
    username: str
    password: str
    upload_directory: str

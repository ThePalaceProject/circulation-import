from __future__ import annotations

import inspect
import logging
import logging.config
import os
from typing import BinaryIO
from typing import Dict
from typing import Union

from attr import dataclass
from ruamel.yaml import YAML
from ruamel.yaml import yaml_object

from circulation_import.errors import BaseError

_logger = logging.getLogger(__name__)

yaml = YAML()


class ConfigurationError(BaseError):
    """Error raised in the case of issues found in the configuration"""


@dataclass(kw_only=True)
@yaml_object(yaml)
class Configuration:
    @staticmethod
    def _restore_missing_default_properties(config: Configuration) -> None:
        members = inspect.getmembers(config)

        for name, member in members:
            if isinstance(member, Configuration):
                klass = type(member)
                arguments = member.__dict__

                if '__len__' in arguments:
                    del arguments['__len__']

                fixed_instance = klass(**arguments)  # type: ignore

                setattr(config, name, fixed_instance)

                Configuration._restore_missing_default_properties(member)

    @classmethod
    def load(cls, filename: str = 'config.yml') -> Configuration:
        current_workdir = os.path.join(os.getcwd())
        filename = os.path.join(current_workdir, filename)
        try:
            with open(filename, 'r') as file:
                # NOTE: This magic is essential for new instance to be properly decorated
                config = cls(**yaml.load(file.read()).__dict__)  # type: ignore

                Configuration._restore_missing_default_properties(config)

            return config
        except (FileNotFoundError, IsADirectoryError):
            _logger.fatal(f'Configuration file "{filename}" not found, exiting!')
            raise ConfigurationError(f'Configuration file "{filename}" not found')

    def save(self, file: Union[str, BinaryIO]) -> None:

        if isinstance(file, str):
            with open(file, 'w') as file:  # type: ignore
                yaml.dump(self, file)
        else:
            yaml.dump(self, file)


@dataclass(kw_only=True)
@yaml_object(yaml)
class LoggingConfiguration:
    handlers: Dict[str, Dict]

    @classmethod
    def load(cls, filename: str = 'logging-config.yml') -> LoggingConfiguration:
        current_workdir = os.path.join(os.getcwd())
        filename = os.path.join(current_workdir, filename)
        try:
            with open(filename, 'r') as file:
                config = yaml.load(file.read())
                return config
        except (FileNotFoundError, IsADirectoryError):
            raise ConfigurationError(f'Logging config file "{filename}" not found, exiting!')

    def apply(self):
        logging.config.dictConfig(self.__dict__)


def load_logging_configuration(logging_configuration_file: str) -> None:
    logging_configuration = LoggingConfiguration.load(logging_configuration_file)
    logging_configuration.apply()

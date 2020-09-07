import logging

import click

from circulation_import.configuration import load_logging_configuration
from circulation_import.server.configuration import ServerConfiguration
from circulation_import.server.importer import Importer
from circulation_import.server.server import Server
from circulation_import.server.storage import ServerStorage
from circulation_import.storage.storage import DbSessionFactory


def _load_server_configuration(server_configuration_file: str) -> ServerConfiguration:
    logging.info(f'Started loading server\'s configuration from {server_configuration_file}')

    server_configuration = ServerConfiguration.load(server_configuration_file)

    logging.info(f'Finished loading server\'s configuration from {server_configuration_file}')

    return server_configuration


@click.group()
@click.pass_context
def server(*args, **kwargs) -> None:  # type: ignore
    """Contains operations which should be executed by a hosting provider"""
    pass


@server.command()
@click.option(
    '--configuration-file',
    '-cf',
    help='Full path to the file containing client\'s configuration',
    required=True,
    type=str
)
@click.option(
    '--logging-configuration-file',
    '-lcf',
    help='Full path to the file containing client\'s logging configuration',
    required=True,
    type=str
)
def monitor(configuration_file: str, logging_configuration_file: str) -> None:
    """Imports the specified collection into Circulation Manager"""
    load_logging_configuration(logging_configuration_file)

    logging.info('Started the import process')

    server_configuration = _load_server_configuration(configuration_file)
    session_factory = DbSessionFactory[ServerStorage](server_configuration.database_configuration)
    importer = Importer(server_configuration.importer_configuration)

    with session_factory.create() as storage:
        server_instance = Server(server_configuration, storage, importer)
        server_instance.run()

        logging.info('Finished the import process')

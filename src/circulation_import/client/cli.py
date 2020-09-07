import logging

import click

from circulation_import.client.client import Client
from circulation_import.client.configuration import ClientConfiguration
from circulation_import.client.configuration import CollectionConfiguration
from circulation_import.configuration import load_logging_configuration
from circulation_import.metadata.serialization import CollectionImportMetadataCSVSerializer
from circulation_import.sftp.client import SFTPClient
from circulation_import.storage.model import MetadataFormat


def _load_client_configuration(client_configuration_file: str) -> ClientConfiguration:
    logging.info(f'Started loading client\'s configuration from {client_configuration_file}')

    client_configuration = ClientConfiguration.load(client_configuration_file)

    logging.info(f'Finished loading client\'s configuration from {client_configuration_file}')

    return client_configuration


@click.group()
@click.pass_context
def client(*args, **kwargs) -> None:  # type: ignore
    """Contains operations which should be executed by a content owner"""


@client.command(name='import')
@click.option('--collection-name', '-c', help='Name of the collection', required=True, type=str)
@click.option('--data-source-name', '-d', help='Name of the data source', required=True, type=str)
@click.option('--books-directory', '-bd', help='Full path to the directory containing books', required=True, type=str)
@click.option('--covers-directory', '-cd', help='Full path to the directory containing covers', required=True, type=str)
@click.option(
    '--reports-directory',
    '-rd',
    help='Full path to the directory containing reports',
    required=True,
    type=str
)
@click.option(
    '--metadata-file',
    '-mf',
    help='Full path to the file containing collection\'s metadata',
    required=True,
    type=str
)
@click.option(
    '--metadata-format',
    '-f',
    help='Metadata format',
    required=True,
    type=click.Choice(list(map(lambda x: x.value, MetadataFormat)), case_sensitive=False)
)
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
def run_import(
        collection_name: str,
        data_source_name: str,
        books_directory: str,
        covers_directory: str,
        reports_directory: str,
        metadata_file: str,
        metadata_format: MetadataFormat,
        configuration_file: str,
        logging_configuration_file: str) -> None:
    """Imports the specified collection into Circulation Manager"""
    load_logging_configuration(logging_configuration_file)

    logging.info('Started the import process')

    client_configuration = _load_client_configuration(configuration_file)
    sftp_client = SFTPClient(client_configuration.sftp_configuration)
    report_serializer = CollectionImportMetadataCSVSerializer()
    client_instance = Client(client_configuration, sftp_client, report_serializer)
    collection_configuration = CollectionConfiguration(
        collection_name=collection_name,
        data_source_name=data_source_name,
        books_directory=books_directory,
        covers_directory=covers_directory,
        reports_directory=reports_directory,
        metadata_file=metadata_file,
        metadata_format=metadata_format
    )

    client_instance.run(collection_configuration)

    logging.info('Finished the import process')

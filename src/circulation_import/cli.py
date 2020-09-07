import logging
import sys
from types import TracebackType
from typing import Type

import click

from circulation_import.client.cli import client
from circulation_import.server.cli import server


def excepthook(
        exception_type: Type[BaseException],
        exception_instance: BaseException,
        exception_traceback: TracebackType) -> None:
    """Function called for uncaught exceptions
    :param exception_type: Type of an exception
    :param exception_instance: Exception instance
    :param exception_traceback: Exception traceback
    """
    logging.fatal(
        f'Exception hook has been fired: {exception_instance}',
        exc_info=(exception_type, exception_instance, exception_traceback))


sys.excepthook = excepthook


@click.group()
@click.pass_context
def cli(*args, **kwargs) -> None:  # type: ignore
    """circulation-import is an application simplifying
    the process of importing book collections into Circulation Manager"""
    pass


cli.add_command(client)
cli.add_command(server)

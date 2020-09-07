import datetime
import logging
import os
import platform
import time
from typing import Any
from typing import Callable
from typing import Tuple

from circulation_import.errors import FatalError
from circulation_import.hash import HasherFactory
from circulation_import.hash import HashingAlgorithm


def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return datetime.datetime.fromtimestamp(os.path.getctime(path_to_file))
    else:
        stat = os.stat(path_to_file)
        try:
            return datetime.datetime.fromtimestamp(stat.st_birthtime)
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return datetime.datetime.fromtimestamp(stat.st_mtime)


def fail(message: str) -> None:
    logging.fatal(message)

    raise FatalError(message)


def retry(
        retries: int,
        delay: datetime.timedelta,
        callback: Callable,
        fail_callback: Callable[[Exception], None] = None) -> Tuple[bool, Any]:
    logger = logging.getLogger(__name__)

    for i in range(retries):
        try:
            logger.debug(f'Attempt # {i + 1}/{retries} started')

            result = callback()

            logger.debug(f'Attempt # {i + 1}/{retries} succeeded')

            return True, result
        except Exception as exception:
            logger.exception(f'Attempt # {i + 1}/{retries} failed')

            if fail_callback:
                fail_callback(exception)

        time.sleep(delay.total_seconds())

    return False, None


def get_file_content(file_path: str) -> bytes:
    logging.debug(f'Started fetching content of {file_path}')

    with open(file_path, 'rb') as file:
        file_content = file.read()

        logging.debug(f'Finished fetching content of {file_path}')

        return file_content


def calculate_file_hash(file_path: str, hashing_algorithm: HashingAlgorithm = HashingAlgorithm.SHA1) -> str:
    logging.debug(f'Started calculating hash of {file_path}')

    file_content = get_file_content(file_path)
    hasher_factory = HasherFactory()
    hasher = hasher_factory.create(hashing_algorithm)
    file_hash = hasher.hash(file_content)

    logging.debug(f'Finished calculating hash of {file_path}: {file_hash}')

    return file_hash

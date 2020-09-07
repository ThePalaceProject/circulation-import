import hashlib
from abc import ABC
from abc import abstractmethod
from enum import Enum

from circulation_import.errors import BaseError


class HashingAlgorithm(Enum):
    MD5 = 'MD5'
    SHA1 = 'SHA-1'


class HashingError(BaseError):
    """Raised in the case of errors occurred during hashing"""


class Hasher(ABC):
    """Base class for all implementations of different hashing algorithms"""

    def __init__(self, hashing_algorithm):
        """Initializes a new instance of Hasher class

        :param hashing_algorithm: Hashing algorithm
        :type hashing_algorithm: HashingAlgorithm
        """
        self._hashing_algorithm = hashing_algorithm

    @abstractmethod
    def hash(self, value):
        raise NotImplementedError()


class UniversalHasher(Hasher):
    def hash(self, value):
        if self._hashing_algorithm in [HashingAlgorithm.MD5, HashingAlgorithm.MD5.value]:
            return hashlib.md5(value).hexdigest()
        elif self._hashing_algorithm in [HashingAlgorithm.SHA1, HashingAlgorithm.SHA1.value]:
            return hashlib.sha1(value).hexdigest()
        else:
            raise HashingError('Unknown hashing algorithm {0}'.format(self._hashing_algorithm))


class HasherFactory(object):
    def create(self, hashing_algorithm):
        return UniversalHasher(hashing_algorithm)

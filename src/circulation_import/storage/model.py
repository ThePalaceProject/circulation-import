import datetime
import os
from enum import Enum

from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship

from circulation_import.storage.storage import Base


class ProcessingStatus(Enum):
    NEW = 'NEW'
    IN_PROGRESS = 'IN_PROGRESS'
    PROCESSED = 'PROCESSED'
    FAILED = 'FAILED'


class MetadataFormat(Enum):
    ONIX = 'onix'
    MARC = 'marc'


class BookMetadata(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey('collections.id'))
    collection = relationship('CollectionMetadata', back_populates='books')
    name = Column(String(255), nullable=False, unique=True)
    hash = Column(String, nullable=False, unique=False)
    status = Column(String(32), nullable=False, unique=False, default=ProcessingStatus.NEW.value)
    error = Column(String(255), nullable=True, unique=False)

    def __init__(self, name: str, _hash: str) -> None:
        self.name = name
        self.hash = _hash
        self.status = ProcessingStatus.NEW.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BookMetadata):
            return False

        return \
            self.name == other.name and \
            self.hash == other.hash and \
            self.status == other.status and \
            self.error == other.error

    @property
    def full_path(self) -> str:
        return os.path.join(
            self.collection.books_directory,
            self.name
        )


class CollectionMetadata(Base):
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    data_source_name = Column(String(255), nullable=False, unique=True)
    timestamp = Column(TIMESTAMP, nullable=False)
    status = Column(String(32), nullable=False, unique=False, default=ProcessingStatus.NEW.value)
    books_directory = Column(String(255), nullable=False, unique=False)
    covers_directory = Column(String(255), nullable=False, unique=False)
    reports_directory = Column(String(255), nullable=False, unique=False)
    metadata_file = Column(String(255), nullable=False, unique=False)
    metadata_format = Column(String(255), nullable=False, unique=False)
    books = relationship('BookMetadata', back_populates='collection')

    def __init__(
            self,
            collection_name: str,
            data_source_name: str,
            timestamp: datetime.datetime,
            books_directory: str,
            covers_directory: str,
            reports_directory: str,
            metadata_file: str,
            metadata_format: MetadataFormat) -> None:
        self.name = collection_name
        self.data_source_name = data_source_name
        self.timestamp = timestamp
        self.status = ProcessingStatus.NEW.value
        self.books_directory = books_directory
        self.covers_directory = covers_directory
        self.reports_directory = reports_directory
        self.metadata_file = metadata_file
        self.metadata_format = metadata_format

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CollectionMetadata):
            return False

        return \
            self.name == other.name and \
            self.status == other.status and \
            self.books == other.books

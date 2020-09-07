from circulation_import.metadata.configuration import BookImportMetadata
from circulation_import.metadata.configuration import CollectionImportMetadata
from circulation_import.storage.model import BookMetadata
from circulation_import.storage.model import CollectionMetadata
from circulation_import.storage.storage import DbStorage


class ServerStorage(DbStorage):
    def find_collection(self, collection_import_metadata: CollectionImportMetadata) -> CollectionMetadata:
        existing_collection = self \
            .query(CollectionMetadata) \
            .filter(CollectionMetadata.name == collection_import_metadata.collection_name) \
            .filter(CollectionMetadata.data_source_name == collection_import_metadata.data_source_name) \
            .one_or_none()

        return existing_collection

    def find_book(self, collection: CollectionMetadata, book_import_metadata: BookImportMetadata) -> BookMetadata:
        existing_book = self \
            .query(BookMetadata) \
            .join(CollectionMetadata) \
            .filter(BookMetadata.collection_id == collection.id) \
            .filter(BookMetadata.name == book_import_metadata.name) \
            .filter(BookMetadata.hash == book_import_metadata.hash) \
            .one_or_none()

        return existing_book

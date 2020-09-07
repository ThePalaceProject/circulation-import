import datetime
import logging
import os
from contextlib import contextmanager
from typing import Any
from typing import Callable
from typing import Generic
from typing import Optional
from typing import Type
from typing import TypeVar

import sqlalchemy.orm
import typing_inspect
from sqlalchemy.engine import Engine
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_repr import RepresentableBase

from circulation_import import utils
from circulation_import.storage.configuration import DatabaseConfiguration
from circulation_import.storage.configuration import DatabaseDriver

Session = sessionmaker()
Base = declarative_base(cls=RepresentableBase)


class DbStorage(sqlalchemy.orm.Session):
    def __init__(
        self,
        bind=None,
        autoflush=True,
        expire_on_commit=True,
        _enable_transaction_accounting=True,
        autocommit=False,
        twophase=False,
        weak_identity_map=None,
        binds=None,
        extension=None,
        enable_baked_queries=True,
        info=None,
        query_cls=None,
    ) -> None:
        super().__init__(
            bind,
            autoflush,
            expire_on_commit,
            _enable_transaction_accounting,
            autocommit,
            twophase,
            weak_identity_map,
            binds,
            extension,
            enable_baked_queries,
            info,
            query_cls)

    def commit(self) -> None:
        original_commit = super().commit
        DbStorage.retry(lambda: original_commit())

    @staticmethod
    def retry(
        callback: Callable,
            fail_callback: Callable[[Exception], None] = None,
            retries: int = 50,
            delay: datetime.timedelta = datetime.timedelta(seconds=3)) -> Any:
        success, result = utils.retry(
            retries,
            delay,
            callback,
            fail_callback
        )

        if not success:
            utils.fail('Could not execute a callback')

        return result


TStorage = TypeVar('TStorage', bound=DbStorage)


class DbFactory(Generic[TStorage]):
    def __init__(self, config: DatabaseConfiguration) -> None:
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._config: DatabaseConfiguration = config
        self._engine: Optional[Engine] = None

    def _create_engine(self) -> Engine:
        self._logger.info(f'Started creating a new engine using the following settings: {self._config}')

        connection_string = self._config.connection_string
        engine = create_engine(
            connection_string,
            echo=self._config.echo,
            isolation_level=self._config.isolation_level,
            poolclass=self._config.pool_class,
            pool_recycle=self._config.pool_recycle,
            pool_pre_ping=self._config.pool_pre_ping,
            connect_args={'check_same_thread': False}
        )

        if self._config.driver == DatabaseDriver.SQLITE.value:
            os.makedirs(os.path.dirname(self._config.database), exist_ok=True)

        Base.metadata.create_all(engine)

        self._logger.info('New engine has been successfully created')

        return engine

    def _get_engine(self) -> Engine:
        if self._engine is None:
            self._engine = self._create_engine()

        return self._engine


class DbSessionFactory(DbFactory[TStorage]):
    def _get_storage_class(self) -> Type[TStorage]:
        generic_type = typing_inspect.get_generic_type(self)
        type_parameters = typing_inspect.get_args(generic_type)

        return type_parameters[0]

    def _create_session(self) -> sqlalchemy.orm.Session:
        engine = self._get_engine()
        storage_class = self._get_storage_class()
        session = storage_class(bind=engine, expire_on_commit=False)

        return session

    @contextmanager
    def create(self) -> TStorage:
        self._logger.info('Started creating a new session')

        session = self._create_session()

        self._logger.info('New session has been successfully created')

        try:
            yield session

            self._logger.info('New session has been successfully used')

            session.commit()

            self._logger.info('New session has been successfully committed')
        except Exception:
            self._logger.exception(f'An unexpected exception occurred during working with session {session}')
            session.rollback()
            self._logger.info('New session has been successfully rolled back')
            raise
        finally:
            session.close()

            self._logger.info('New session has been successfully closed')

from enum import Enum
from typing import Optional

from attr import dataclass
from ruamel.yaml import yaml_object
from sqlalchemy.pool import QueuePool

from circulation_import.configuration import Configuration
from circulation_import.configuration import yaml


class DatabaseDriver(Enum):
    SQLITE = 'sqlite'


@dataclass(kw_only=True)
@yaml_object(yaml)
class DatabaseConfiguration(Configuration):
    driver: str = DatabaseDriver.SQLITE.value
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: str
    echo: bool = False
    isolation_level: str = 'READ UNCOMMITTED'
    pool_class = QueuePool
    pool_recycle: int = 3600
    pool_pre_ping: bool = True

    @property
    def connection_string(self) -> str:
        if self.driver == DatabaseDriver.SQLITE.value:
            return f'{self.driver}:///{self.database}'
        else:
            return f'{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'

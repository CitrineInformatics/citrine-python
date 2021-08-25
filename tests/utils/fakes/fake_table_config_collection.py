from uuid import uuid4, UUID
from typing import List, Tuple, Optional, Union

from gemd.entity.link_by_uid import LinkByUID

from citrine.gemtables.columns import Column
from citrine.gemtables.variables import Variable

from citrine._session import Session
from citrine.exceptions import NotFound
from citrine.resources.material_run import MaterialRun
from citrine.resources.table_config import TableConfig, TableConfigCollection, TableBuildAlgorithm


class TableConfigVersionStorage:
    """Helper class to store multiple versions of a table config."""
    def __init__(self):
        self._configs = {}

    def add_config(self, table_config: TableConfig):
        versions = self._configs.setdefault(str(table_config.uid), {})
        versions[table_config.version_number] = table_config

    def get_config(self, uid: Union[str, UUID], version: Optional[int] = None):
        if version is None:
            return self.get_latest_version(uid)
        elif str(uid) not in self._configs:
            return None
        else:
            versions = self._configs[str(uid)]
            return versions.get(version, None)

    def get_latest_version(self, uid: Union[str, UUID]):
        if str(uid) not in self._configs:
            return None
        else:
            versions = self._configs[str(uid)]
            latest_version = max(versions, key=versions.get)
            return versions[latest_version]

    def get_all(self):
        return [self.get_latest_version(uid) for uid in self._configs.keys()]


class FakeTableConfigCollection(TableConfigCollection):

    def __init__(self, project_id: UUID, session: Session):
        super().__init__(project_id, session)
        self._storage = TableConfigVersionStorage()

    def get(self, uid: Union[UUID, str], *, version: Optional[int] = None):
        config = self._storage.get_config(uid, version)
        if config is None:
            raise NotFound(f"Cannot find table config with uid={uid}")
        return config

    def register(self, table_config: TableConfig) -> TableConfig:
        if table_config.config_uid is None:
            table_config.config_uid = uuid4()

        table_config.version_uid = uuid4()
        if table_config.version_number is not None:
            table_config.version_number += 1
        else:
            table_config.version_number = 1

        # Add version to storage
        self._storage.add_config(table_config)

        return table_config

    def list(self, page: Optional[int] = None, per_page: int = 100):
        configs = self._storage.get_all()
        if page is None:
            return configs
        else:
            return configs[(page - 1)*per_page:page*per_page]

    def default_for_material(
        self, *,
        material: Union[MaterialRun, LinkByUID, str, UUID],
        name: str,
        description: str = None,
        algorithm: Optional[TableBuildAlgorithm] = None,
        scope: str = None
    ) -> Tuple[TableConfig, List[Tuple[Variable, Column]]]:
        table_config = TableConfig(
            name=name, description=description, datasets=[],
            rows=[], variables=[], columns=[]
        )
        return table_config, []

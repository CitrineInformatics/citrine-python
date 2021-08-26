from uuid import uuid4, UUID
from typing import List, Dict, Tuple, Optional, Union, Iterable, TypeVar, Generic

from gemd.entity.link_by_uid import LinkByUID

from citrine._session import Session
from citrine.exceptions import NotFound
from citrine.resources.material_run import MaterialRun
from citrine.resources.gemtables import GemTable, GemTableCollection
from citrine.resources.table_config import TableConfig, TableConfigCollection, TableBuildAlgorithm

from citrine.gemtables.columns import Column
from citrine.gemtables.variables import Variable

from tests.utils.functions import normalize_uid

ResourceType = TypeVar('ResourceType', bound='Resource')


class VersionedResourceStorage(Generic[ResourceType]):
    """Helper class to store multiple versions of an object."""

    def __init__(self):
        self._resources = {}

    @property
    def resources(self) -> Dict[UUID, Dict[int, ResourceType]]:
        return self._resources

    def register(self, resource: ResourceType, *, version: int) -> None:
        uid = normalize_uid(resource.uid)
        versions = self.resources.setdefault(uid, {})
        versions[version] = resource

    def _get_latest(self, uid: UUID) -> ResourceType:
        uid = normalize_uid(uid)
        versions = self.resources[uid]
        latest_version = max(versions.keys())
        return versions[latest_version]

    def get(self, uid: Union[str, UUID], *, version: Optional[int] = None) -> Optional[ResourceType]:
        uid = normalize_uid(uid)
        if uid not in self.resources:
            return None
        elif version is None:
            return self._get_latest(uid)
        else:
            versions = self.resources[uid]
            return versions.get(version, None)

    def list_by_uid(self, uid: Union[str, UUID]) -> List[ResourceType]:
        uid = normalize_uid(uid)
        versions = self.resources.get(uid, {})
        sorted_versions = sorted(versions.keys())
        return [versions[v] for v in sorted_versions]

    def list_latest(self) -> List[ResourceType]:
        return [self._get_latest(uid) for uid in self.resources.keys()]


class FakeTableConfigCollection(TableConfigCollection):

    def __init__(self, project_id: UUID, session: Session):
        super().__init__(project_id, session)
        self._storage = VersionedResourceStorage[TableConfig]()

    def get(self, uid: Union[UUID, str], *, version: Optional[int] = None):
        config = self._storage.get(uid, version=version)
        if config is None:
            raise NotFound("")
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
        self._storage.register(table_config, version=table_config.version_number)

        return table_config

    def list(self, page: Optional[int] = None, per_page: int = 100) -> Iterable[TableConfig]:
        configs = self._storage.list_latest()
        if page is None:
            return iter(configs)
        else:
            return iter(configs[(page - 1)*per_page:page*per_page])

    def default_for_material(
        self, *,
        material: Union[MaterialRun, LinkByUID, str, UUID],
        name: str,
        description: str = None,
        algorithm: Optional[TableBuildAlgorithm] = None,
        scope: str = None
    ) -> Tuple[TableConfig, List[Tuple[Variable, Column]]]:
        table_config = TableConfig(
            name=name, description="", datasets=[],
            rows=[], variables=[], columns=[]
        )
        return table_config, []


class FakeGemTableCollection(GemTableCollection):

    def __init__(self, project_id: UUID, session: Session):
        super().__init__(project_id, session)
        self._config_map = {}  # Map config UID to table UID
        self._table_storage = VersionedResourceStorage[GemTable]()

    def build_from_config(self, config: Union[TableConfig, str, UUID], *,
                          version: Union[str, int] = None,
                          timeout: float = 15 * 60) -> GemTable:
        if isinstance(config, TableConfig):
            config_uid = config.config_uid
        else:
            config_uid = normalize_uid(config)

        # Find existing table matching UID
        table_id = self._config_map.setdefault(config_uid, uuid4())
        latest_table = self._table_storage.get(table_id)
        new_version = latest_table.version + 1 if latest_table is not None else 1

        # Create new table w/ new version
        table = GemTable()
        table.uid = table_id
        table.version = new_version
        table.download_url = "https://citrine-platform-fake.com"
        self._table_storage.register(table, version=table.version)

        return table

    def list_by_config(self, table_config_uid: UUID,
                       *,
                       page: Optional[int] = None,
                       per_page: int = 100) -> Iterable[GemTable]:
        config_uid = normalize_uid(table_config_uid)
        if config_uid not in self._config_map:
            return iter([])
        else:
            table_id = self._config_map[config_uid]
            return self.list_versions(table_id, page=page, per_page=per_page)

    def list_versions(self,
                      uid: UUID,
                      *,
                      page: Optional[int] = None,
                      per_page: int = 100) -> Iterable[GemTable]:
        tables = self._table_storage.list_by_uid(uid)
        if page is None:
            return iter(tables)
        else:
            return iter(tables[(page - 1)*per_page:page*per_page])

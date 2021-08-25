from uuid import uuid4, UUID
from typing import Iterable, Optional, Union

from citrine._session import Session
from citrine.resources.gemtables import GemTable, GemTableCollection
from citrine.resources.table_config import TableConfig


class FakeGemTableCollection(GemTableCollection):

    def __init__(self, project_id: UUID, session: Session):
        super().__init__(project_id, session)
        self._tables = {}

        table = GemTable()
        table.uid = uuid4()
        table.version = 1
        table.download_url = "https://citrine-platform-fake.com"
        self._default_table = table

    def build_from_config(self, config: Union[TableConfig, str, UUID], *,
                          version: Union[str, int] = None,
                          timeout: float = 15 * 60) -> GemTable:
        return self._default_table

    def list_by_config(self,
                       table_config_uid: UUID,
                       *,
                       page: Optional[int] = None,
                       per_page: int = 100) -> Iterable[GemTable]:
        return iter([self._default_table])

    def list_versions(self,
                      uid: UUID,
                      *,
                      page: Optional[int] = None,
                      per_page: int = 100) -> Iterable[GemTable]:
        return iter([self._default_table])

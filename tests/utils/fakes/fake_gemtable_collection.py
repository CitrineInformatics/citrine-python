from uuid import UUID
from typing import Iterable, Optional, Union

from citrine.resources.gemtables import GemTable, GemTableCollection
from citrine.resources.table_config import TableConfig


class FakeGemTableCollection(GemTableCollection):

    def build_from_config(self, config: Union[TableConfig, str, UUID], *,
                          version: Union[str, int] = None,
                          timeout: float = 15 * 60) -> GemTable:
        pass

    def list_by_config(self,
                       table_config_uid: UUID,
                       *,
                       page: Optional[int] = None,
                       per_page: int = 100) -> Iterable[GemTable]:
        pass
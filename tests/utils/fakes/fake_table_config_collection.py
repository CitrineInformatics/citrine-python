from uuid import UUID
from typing import List, Tuple, Optional, Union

from gemd.entity.link_by_uid import LinkByUID

from citrine.gemtables.columns import Column
from citrine.gemtables.variables import Variable

from citrine.resources.material_run import MaterialRun
from citrine.resources.table_config import TableConfig, TableConfigCollection, TableBuildAlgorithm


class FakeTableConfigCollection(TableConfigCollection):

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

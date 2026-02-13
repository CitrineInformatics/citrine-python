from typing import List, Union, Optional
from uuid import UUID

from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties
from citrine.informatics.design_spaces.top_level_design_space import TopLevelDesignSpace
from citrine.informatics.design_spaces.design_space_settings import DesignSpaceSettings
from citrine.informatics.design_spaces.subspace import DesignSubspace
from citrine.informatics.dimensions import Dimension

__all__ = ['ProductDesignSpace']


class ProductDesignSpace(EngineResource['ProductDesignSpace'], TopLevelDesignSpace):
    """A Cartesian product of design spaces.

    Factors can be other design spaces and/or univariate dimensions.

    Parameters
    ----------
    name:str
        the name of the design space
    description:str
        the description of the design space
    subspaces: list[Union[UUID, DesignSubspace]]
        the list of subspaces to combine, defined in-line
    dimensions: list[Dimension]
        univariate dimensions that are factors of the design space; can be enumerated or continuous

    """

    _settings = properties.Optional(properties.Object(DesignSpaceSettings), "metadata.settings")

    subspaces = properties.List(properties.Object(DesignSubspace), 'data.instance.subspaces',
                                default=[])
    dimensions = properties.Optional(
        properties.List(properties.Object(Dimension)), 'data.instance.dimensions'
    )

    typ = properties.String('data.instance.type', default='ProductDesignSpace',
                            deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 subspaces: Optional[list[Union[UUID, DesignSubspace]]] = None,
                 dimensions: Optional[list[Dimension]] = None):
        self.name: str = name
        self.description: str = description
        self.subspaces: list[Union[UUID, DesignSubspace]] = subspaces or []
        self.dimensions: list[Dimension] = dimensions or []

    def _post_dump(self, data: dict) -> dict:
        data = super()._post_dump(data)

        if self._settings:
            data["settings"] = self._settings.dump()

        return data

    def __str__(self):
        return '<ProductDesignSpace {!r}>'.format(self.name)

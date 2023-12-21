from typing import List, Union, Optional
from uuid import UUID

from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties
from citrine.informatics.design_spaces.design_space import DesignSpace
from citrine.informatics.dimensions import Dimension

__all__ = ['ProductDesignSpace']


class ProductDesignSpace(EngineResource['ProductDesignSpace'], DesignSpace):
    """A Cartesian product of design spaces.

    Factors can be other design spaces and/or univariate dimensions.

    Parameters
    ----------
    name:str
        the name of the design space
    description:str
        the description of the design space
    subspaces: List[Union[UUID, DesignSpace]]
        the list of subspaces to combine, either design spaces defined in-line
        or UUIDs that reference design spaces on the platform
    dimensions: list[Dimension]
        univariate dimensions that are factors of the design space; can be enumerated or continuous

    """

    subspaces = properties.List(properties.Object(DesignSpace), 'data.instance.subspaces',
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
                 subspaces: Optional[List[Union[UUID, DesignSpace]]] = None,
                 dimensions: Optional[List[Dimension]] = None):
        self.name: str = name
        self.description: str = description
        self.subspaces: List[Union[UUID, DesignSpace]] = subspaces or []
        self.dimensions: List[Dimension] = dimensions or []

    def _post_dump(self, data: dict) -> dict:
        data = super()._post_dump(data)
        for i, subspace in enumerate(data['instance']['subspaces']):
            if isinstance(subspace, dict):
                # embedded design spaces are not modules, so only serialize their config
                data['instance']['subspaces'][i] = subspace['instance']
        return data

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        for i, subspace_data in enumerate(data['data']['instance']['subspaces']):
            if isinstance(subspace_data, dict):
                data['data']['instance']['subspaces'][i] = DesignSpace.wrap_instance(subspace_data)
        return data

    def __str__(self):
        return '<ProductDesignSpace {!r}>'.format(self.name)

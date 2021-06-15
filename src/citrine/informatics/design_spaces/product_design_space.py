from typing import List, Union, Optional
from uuid import UUID
from copy import deepcopy

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine.informatics.design_spaces.design_space import DesignSpace
from citrine.informatics.dimensions import Dimension
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['ProductDesignSpace']


class ProductDesignSpace(Resource['ProductDesignSpace'], DesignSpace, AIResourceMetadata):
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

    _resource_type = ResourceTypeEnum.MODULE

    subspaces = properties.List(properties.Union(
        [properties.UUID, properties.Object(DesignSpace)]
    ), 'config.subspaces', default=[])
    dimensions = properties.Optional(
        properties.List(properties.Object(Dimension)), 'config.dimensions'
    )
    # Product design spaces should not be embedded in other subspaces, hence status is required
    status = properties.String('status', serializable=False)

    typ = properties.String('config.type', default='ProductDesignSpace', deserializable=False)
    module_type = properties.String('module_type', default='DESIGN_SPACE')

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

    def dump(self) -> dict:
        """Override dump to replace on-platform subspaces with their uids."""
        model_copy = deepcopy(self)
        for i, subspace in enumerate(model_copy.subspaces):
            if isinstance(subspace, DesignSpace) and subspace.uid is not None:
                model_copy.subspaces[i] = subspace.uid
        serialized = properties.Object(ProductDesignSpace).serialize(model_copy)
        return self._post_dump(serialized)

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        for i, subspace in enumerate(data['config']['subspaces']):
            if isinstance(subspace, dict):
                # embedded design spaces are not modules, so only serialize their config
                data['config']['subspaces'][i] = subspace['config']
        return data

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        subspaces = data['config'].get('subspaces', [])
        # For each subspace, rename the `instance` key to `config`.
        for i, _ in enumerate(subspaces):
            data['config']['subspaces'][i]['config'] = \
                data['config']['subspaces'][i].pop('instance')
        return data

    def __str__(self):
        return '<ProductDesignSpace {!r}>'.format(self.name)

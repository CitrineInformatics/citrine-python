from typing import List
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.informatics.design_spaces.design_space import DesignSpace
from citrine.informatics.dimensions import Dimension

__all__ = ['ProductDesignSpace']


class ProductDesignSpace(Resource['ProductDesignSpace'], DesignSpace):
    """[ALPHA] An outer product of univariate dimensions, either continuous or enumerated.

    Parameters
    ----------
    name:str
        the name of the design space
    description:str
        the description of the design space
    dimensions: list[Dimension]
        univariate dimensions that are factors of the design space; can be enumerated or continuous

    """

    _response_key = None

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')
    dimensions = properties.List(properties.Object(Dimension), 'config.dimensions')
    typ = properties.String('config.type', default='Univariate', deserializable=False)
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    archived = properties.Boolean('archived', default=False)
    experimental = properties.Boolean("experimental", serializable=False, default=True)
    experimental_reasons = properties.Optional(
        properties.List(properties.String()),
        'experimental_reasons',
        serializable=False
    )

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='DESIGN_SPACE')
    schema_id = properties.UUID('schema_id', default=UUID('6c16d694-d015-42a7-b462-8ef299473c9a'))

    def __init__(self,
                 name: str,
                 description: str,
                 dimensions: List[Dimension],
                 session: Session = Session()):
        self.name: str = name
        self.description: str = description
        self.dimensions: List[Dimension] = dimensions
        self.session: Session = session

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<ProductDesignSpace {!r}>'.format(self.name)

"""Tools for working with Capabilities."""
from typing import List, Type
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.dimensions import Dimension

__all__ = ['Capability', 'ProductCapability']


class Capability(PolymorphicSerializable['Capability']):
    """A module representing a material domain."""

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the sole currently implemented subtype."""
        return ProductCapability


class ProductCapability(Resource['ProductCapability'], Capability):
    """Capability composed of an outer product of univariate dimensions."""

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

    # NOTE: This could go here or in _post_dump - it's unclear which is better right now
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
        return '<ProductCapability {!r}>'.format(self.name)

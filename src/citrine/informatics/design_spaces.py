"""Tools for working with design spaces."""
from typing import Any, List, Mapping, Type
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.dimensions import Dimension
from citrine.informatics.modules import Module

__all__ = ['DesignSpace', 'ProductDesignSpace', 'EnumeratedDesignSpace']


class DesignSpace(Module):
    """[ALPHA] A Citrine Design Space describes the set of materials that can be made.

    Abstract type that returns the proper type given a serialized dict.


    """

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            'Univariate': ProductDesignSpace,
            'EnumeratedDesignSpace': EnumeratedDesignSpace,
        }[data['config']['type']]


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
    active = properties.Boolean('active', default=True)

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


class EnumeratedDesignSpace(Resource['EnumeratedDesignSpace'], DesignSpace):
    """[ALPHA] An explicit enumeration of candidate materials to score.

    Note that every candidate must have exactly the descriptors in the list populated
    (no more, no less) in order to be included.

    Parameters
    ----------
    name:str
        the name of the design space
    description:str
        the description of the design space
    descriptors: list[Descriptor]
        the list of descriptors included in the candidates of the design space
    data: list[dict]
        list of dicts of the shape `{<descriptor_key>: <descriptor_value>}`
        where each dict corresponds to a candidate in the design space

    """

    _response_key = None

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')
    descriptors = properties.List(properties.Object(Descriptor), 'config.descriptors')
    data = properties.List(properties.Mapping(properties.String, properties.Raw), 'config.data')

    typ = properties.String('config.type', default='EnumeratedDesignSpace', deserializable=False)
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    active = properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='DESIGN_SPACE')
    schema_id = properties.UUID('schema_id', default=UUID('f3907a58-aa46-462c-8837-a5aa9605e79e'))

    def __init__(self,
                 name: str,
                 description: str,
                 descriptors: List[Descriptor],
                 data: List[Mapping[str, Any]],
                 session: Session = Session()):
        self.name: str = name
        self.description: str = description
        self.descriptors: List[Descriptor] = descriptors
        self.data: List[Mapping[str, Any]] = data
        self.session: Session = session

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<EnumeratedDesignSpace {!r}>'.format(self.name)

from typing import List, Mapping, Any
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.design_spaces.design_space import DesignSpace

__all__ = ['EnumeratedDesignSpace']


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
    status = properties.Optional(properties.String(), 'status', serializable=False)
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

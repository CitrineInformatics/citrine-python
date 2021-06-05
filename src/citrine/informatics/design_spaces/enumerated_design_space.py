from typing import List, Mapping, Any

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.design_spaces.design_space import DesignSpace
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['EnumeratedDesignSpace']


class EnumeratedDesignSpace(Resource['EnumeratedDesignSpace'], DesignSpace, AIResourceMetadata):
    """An explicit enumeration of candidate materials to score.

    Enumerated design spaces are intended to capture small spaces with fewer than
    1000 values.  For larger spaces, use the DataSourceDesignSpace.

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

    _resource_type = ResourceTypeEnum.MODULE

    descriptors = properties.List(properties.Object(Descriptor), 'config.descriptors')
    data = properties.List(properties.Mapping(properties.String, properties.Raw), 'config.data')

    typ = properties.String('config.type', default='EnumeratedDesignSpace', deserializable=False)
    module_type = properties.String('module_type', default='DESIGN_SPACE')

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 descriptors: List[Descriptor],
                 data: List[Mapping[str, Any]]):
        self.name: str = name
        self.description: str = description
        self.descriptors: List[Descriptor] = descriptors
        self.data: List[Mapping[str, Any]] = data

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<EnumeratedDesignSpace {!r}>'.format(self.name)

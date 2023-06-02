from typing import List, Mapping, Any

from citrine._rest.engine_resource import ModuleEngineResource
from citrine._serialization import properties
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.design_spaces.design_space import DesignSpace

__all__ = ['EnumeratedDesignSpace']


class EnumeratedDesignSpace(ModuleEngineResource['EnumeratedDesignSpace'], DesignSpace):
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

    descriptors = properties.List(properties.Object(Descriptor), 'data.instance.descriptors')
    data = properties.List(properties.Mapping(properties.String, properties.Raw),
                           'data.instance.data')

    typ = properties.String('data.instance.type', default='EnumeratedDesignSpace',
                            deserializable=False)

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

    def __str__(self):
        return '<EnumeratedDesignSpace {!r}>'.format(self.name)

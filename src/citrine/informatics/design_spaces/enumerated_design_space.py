from typing import List, Mapping, Union
from warnings import warn

from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.design_spaces.design_space import DesignSpace

__all__ = ['EnumeratedDesignSpace']


class EnumeratedDesignSpace(EngineResource['EnumeratedDesignSpace'], DesignSpace):
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
    _data = properties.List(properties.Mapping(properties.String,
                                               properties.Union([properties.String(),
                                                                 properties.Integer(),
                                                                 properties.Float()])),
                            'data.instance.data')

    typ = properties.String('data.instance.type', default='EnumeratedDesignSpace',
                            deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 descriptors: List[Descriptor],
                 data: List[Mapping[str, Union[int, float, str]]]):
        self.name: str = name
        self.description: str = description
        self.descriptors: List[Descriptor] = descriptors
        self.data: List[Mapping[str, Union[int, float, str]]] = data

    def __str__(self):
        return '<EnumeratedDesignSpace {!r}>'.format(self.name)

    @property
    def data(self) -> List[Mapping[str, Union[int, float, str]]]:
        """List of dicts corresponding to candidates in the design space."""
        return self._data

    @data.setter
    def data(self, value: List[Mapping[str, Union[int, float, str]]]):
        for item in value:
            for el in item.values():
                if isinstance(el, (int, float)):
                    warn("Providing numeric data values is deprecated as of 3.4.7, and will be "
                         "dropped in 4.0.0. Please use strings instead.",
                         DeprecationWarning)
        self._data = value

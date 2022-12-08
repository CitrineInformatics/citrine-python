"""Tools for working with Processors."""
from typing import Optional, Mapping, Type, List

from citrine._rest.resource import ResourceTypeEnum, Resource
from citrine._rest.ai_resource_metadata import AIResourceMetadata
from citrine._serialization import properties
from citrine.informatics.modules import Module


__all__ = ['Processor', 'GridProcessor', 'EnumeratedProcessor', 'MonteCarloProcessor']


class Processor(Module):
    """A Citrine Processor describes how a design space is searched.

    Abstract type that returns the proper type given a serialized dict.

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    """:Optional[UUID]: Citrine Platform unique identifier"""
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')

    @classmethod
    def get_type(cls, data) -> Type['Processor']:
        """Return the sole currently implemented subtype."""
        return {
            'Grid': GridProcessor,
            'Enumerated': EnumeratedProcessor,
            'ContinuousSearch': MonteCarloProcessor
        }[data['config']['type']]

    def _attrs(self) -> List[str]:
        return ["name", "description", "id"]  # pragma: no cover

    def __eq__(self, other):
        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in self._attrs()
            ])
        except AttributeError:
            return False


class GridProcessor(Resource['GridProcessor'], Processor, AIResourceMetadata):
    """Generates samples from the Cartesian product of finite dimensions, then scans over them.

    For each continuous dimensions, a uniform grid is created between the lower and upper bounds of
    the descriptor. The number of points along each continuous dimension is specified.
    by ``grid_sizes``. No such discretization is necessary for enumerated dimensions,
    because they are finite.

    Be careful when using a grid processor, as the number of points grows exponentially with
    the number of dimensions. For high-dimensional design spaces, a continuous processor
    is often preferable.

    Parameters
    ----------
    name: str
        name of the processor
    description: str
        description of the processor
    grid_sizes: dict[str, int]
        the number of points to select along each continuous dimension, by dimension name

    """

    _resource_type = ResourceTypeEnum.MODULE

    grid_sizes = properties.Mapping(
        properties.String,
        properties.Integer,
        'config.grid_dimensions'
    )

    typ = properties.String('config.type', default='Grid', deserializable=False)
    module_type = properties.String('module_type', default='PROCESSOR')

    def _attrs(self) -> List[str]:
        return ["name", "description", "grid_sizes", "typ"]

    def __init__(self,
                 name: str, *,
                 description: str,
                 grid_sizes: Mapping[str, int]):
        self.name: str = name
        self.description: str = description
        self.grid_sizes: Mapping[str, int] = grid_sizes

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<GridProcessor {!r}>'.format(self.name)


class EnumeratedProcessor(Resource['EnumeratedProcessor'], Processor, AIResourceMetadata):
    """Process a design space by enumerating up to a fixed number of samples from the domain.

    Each sample is processed independently.

    Parameters
    ----------
    name: str
        name of the processor
    description: str
        description of the processor
    max_candidates: int
        maximum number of samples that can be enumerated over (default: 1000)

    """

    _resource_type = ResourceTypeEnum.MODULE

    max_candidates = properties.Integer('config.max_size')

    typ = properties.String('config.type', default='Enumerated', deserializable=False)
    module_type = properties.String('module_type', default='PROCESSOR')

    def _attrs(self) -> List[str]:
        return ["name", "description", "max_candidates", "typ"]

    def __init__(self,
                 name: str, *,
                 description: str,
                 max_candidates: Optional[int] = None):
        self.name: str = name
        self.description: str = description
        self.max_candidates: int = max_candidates or 1000

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<EnumeratedProcessor {!r}>'.format(self.name)


class MonteCarloProcessor(Resource['ContinuousSearch'], Processor, AIResourceMetadata):
    """Using a Monte Carlo optimizer to search for the best candidate.

    The moves that the MonteCarlo optimizer makes are inferred from the descriptors in the
    design space.

    Parameters
    ----------
    name: str
        name of the processor
    description: str
        description of the processor
    max_candidates: int
        maximum number of candidates generated by the processor (default: system configured limit)
    mode: str
        for internal use only

    """

    _resource_type = ResourceTypeEnum.MODULE

    max_candidates = properties.Optional(properties.Integer, 'config.max_candidates')
    mode = properties.Optional(properties.String(), 'config.mode')

    typ = properties.String('config.type', default='ContinuousSearch', deserializable=False)
    module_type = properties.String('module_type', default='PROCESSOR')

    def _attrs(self) -> List[str]:
        return ["name", "description", "mode", "typ"]

    def __init__(self,
                 name: str, *,
                 description: str,
                 max_candidates: Optional[int] = None,
                 mode: Optional[str] = None):
        self.name: str = name
        self.description: str = description
        self.max_candidates: Optional[int] = max_candidates
        self.mode: Optional[str] = mode

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<MonteCarloProcessor {!r}>'.format(self.name)

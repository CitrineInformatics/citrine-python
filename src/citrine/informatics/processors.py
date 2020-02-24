"""Tools for working with Processors."""
from typing import Optional, Mapping, Type
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.modules import Module


__all__ = ['Processor', 'GridProcessor', 'EnumeratedProcessor']


class Processor(Module):
    """[ALPHA] A Citrine Processor describes how a design space is searched.

    Abstract type that returns the proper type given a serialized dict.

    """

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type['Processor']:
        """Return the sole currently implemented subtype."""
        return {
            'Grid': GridProcessor,
            'Enumerated': EnumeratedProcessor
        }[data['config']['type']]


class GridProcessor(Serializable['GridProcessor'], Processor):
    """[ALPHA] Generates samples from the outer product of finite dimensions, then scans over them.

    To create a finite set of materials from continuous dimensions, a uniform grid is created
    between the lower and upper bounds of the descriptor.
    The number of points along each dimension is specified by `grid_sizes`.

    Parameters
    ----------
    name: str
        name of the processor
    description: str
        description of the processor
    grid_sizes: dict[str, int]
        the number of points to select along each dimension of the grid, by dimension name

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')
    typ = properties.String('config.type', default='Grid', deserializable=False)
    grid_sizes = properties.Mapping(
        properties.String,
        properties.Integer,
        'config.grid_dimensions'
    )
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    active = properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='PROCESSOR')
    schema_id = properties.UUID('schema_id', default=UUID('272791a5-5468-4344-ac9f-2811d9266a4d'))

    def __init__(self,
                 name: str,
                 description: str,
                 grid_sizes: Mapping[str, int],
                 session: Optional[Session] = None):
        self.name: str = name
        self.description: str = description
        self.grid_sizes: Mapping[str, int] = grid_sizes
        self.session: Optional[Session] = session

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<GridProcessor {!r}>'.format(self.name)


class EnumeratedProcessor(Serializable['EnumeratedProcessor'], Processor):
    """[ALPHA] Process a design space by enumerating up to a fixed number of samples from the domain.

    Each sample is processed independently.

    Parameters
    ----------
    name: str
        name of the processor
    description: str
        description of the processor
    max_size: int
        maximum number of samples that can be enumerated over

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')
    max_size = properties.Integer('config.max_size')
    typ = properties.String('config.type', default='Enumerated', deserializable=False)
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    active = properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='PROCESSOR')
    schema_id = properties.UUID('schema_id', default=UUID('307b88a2-fd50-4d27-ae91-b8d6282f68f7'))

    def __init__(self,
                 name: str,
                 description: str,
                 max_size: Optional[int] = None,
                 session: Optional[Session] = None):
        self.name: str = name
        self.description: str = description
        self.max_size: int = max_size or 2 ** 31 - 1  # = 2147483647 (max 32-bit integer)
        self.session: Optional[Session] = session

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<EnumeratedProcessor {!r}>'.format(self.name)

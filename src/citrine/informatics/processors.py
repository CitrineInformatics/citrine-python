"""Tools for working with Processors."""
from typing import Optional, Mapping, Type, List
from warnings import warn

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.modules import Module


__all__ = ['Processor', 'GridProcessor', 'EnumeratedProcessor', 'MonteCarloProcessor']


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
    archived = properties.Boolean('archived', default=False)
    experimental = properties.Boolean("experimental", serializable=False, default=True)
    experimental_reasons = properties.Optional(
        properties.List(properties.String()),
        'experimental_reasons',
        serializable=False
    )

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='PROCESSOR')

    def _attrs(self) -> List[str]:
        return ["name", "description", "grid_sizes", "typ"]

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
    max_candidates: int
        maximum number of samples that can be enumerated over (default: 1000)

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')
    max_candidates = properties.Integer('config.max_size')
    typ = properties.String('config.type', default='Enumerated', deserializable=False)
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
    module_type = properties.String('module_type', default='PROCESSOR')

    def _attrs(self) -> List[str]:
        return ["name", "description", "max_size", "typ"]

    def __init__(self,
                 name: str,
                 description: str,
                 max_candidates: Optional[int] = None,
                 max_size: Optional[int] = None,
                 session: Optional[Session] = None):
        if max_candidates is not None and max_size is not None:
            raise ValueError("Both max_candidates and max_size were specified.  "
                             "Please only specify max_candidates.")
        if max_size is not None:
            warn("The max_size argument is deprecated.  Please use max_candidates instead.",
                 DeprecationWarning)
        self.name: str = name
        self.description: str = description
        self.max_candidates: int = max_candidates or max_size or 1000
        self.session: Optional[Session] = session

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<EnumeratedProcessor {!r}>'.format(self.name)

    @property
    def max_size(self):
        """[DEPRECATED] Alias for max_candidates."""
        warn("EnumeratedProcessor.max_size is deprecated.  Please use max_candidates instead",
             DeprecationWarning)
        return self.max_candidates


class MonteCarloProcessor(Serializable['GridProcessor'], Processor):
    """[ALPHA] Using a Monte Carlo optimizer to search for the best candidate.

    The moves that the MonteCarlo optimizer makes are inferred from the descriptors in the
    design space.

    Parameters
    ----------
    name: str
        name of the processor
    description: str
        description of the processor

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')
    typ = properties.String('config.type', default='ContinuousSearch', deserializable=False)
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    experimental = properties.Boolean("experimental", serializable=False, default=True)
    experimental_reasons = properties.Optional(
        properties.List(properties.String()),
        'experimental_reasons',
        serializable=False
    )

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='PROCESSOR')

    def _attrs(self) -> List[str]:
        return ["name", "description", "typ"]

    def __init__(self,
                 name: str,
                 description: str,
                 session: Optional[Session] = None):
        self.name: str = name
        self.description: str = description
        self.session: Optional[Session] = session

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<MonteCarloProcessor {!r}>'.format(self.name)

"""Tools for working with design spaces."""
from typing import Type

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.modules import Module
from citrine._rest.mixin import Mixin

__all__ = ['DesignSpace']


class DesignSpace(Module, Mixin):
    """A Citrine Design Space describes the set of materials that can be made.

    Abstract type that returns the proper type given a serialized dict.

    """

    _response_key = None

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')

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

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        from .data_source_design_space import DataSourceDesignSpace
        from .enumerated_design_space import EnumeratedDesignSpace
        from .formulation_design_space import FormulationDesignSpace
        from .product_design_space import ProductDesignSpace
        return {
            'Univariate': ProductDesignSpace,
            'ProductDesignSpace': ProductDesignSpace,
            'EnumeratedDesignSpace': EnumeratedDesignSpace,
            'FormulationDesignSpace': FormulationDesignSpace,
            'DataSourceDesignSpace': DataSourceDesignSpace
        }[data['config']['type']]

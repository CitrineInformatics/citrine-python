from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine.informatics.design_spaces.design_space import DesignSpace


class DesignSubspace(PolymorphicSerializable["DesignSubspace"], DesignSpace):
    """An individual subspace within a Design Space.

    A DesignSubspace cannot be registered to the Citrine Platform by itself
    and must be included as a component within a ProductDesignSpace or
    HierarchicalDesignSpace to be used.

    """

    name = properties.String("name")
    description = properties.Optional(properties.String(), "description")

    @classmethod
    def get_type(cls, data) -> type['DesignSubspace']:
        """Return the subtype."""
        from .data_source_design_space import DataSourceDesignSpace
        from .formulation_design_space import FormulationDesignSpace

        type_dict = {
            'FormulationDesignSpace': FormulationDesignSpace,
            'DataSourceDesignSpace': DataSourceDesignSpace,
        }

        typ = type_dict.get(data['type'])
        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid design subspace type. '
                'Must be in {}.'.format(data['type'], type_dict.keys())
            )

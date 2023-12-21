from typing import Mapping, Optional, Set

from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties
from citrine.informatics.constraints import Constraint
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.design_spaces.design_space import DesignSpace

__all__ = ['FormulationDesignSpace']


class FormulationDesignSpace(EngineResource['FormulationDesignSpace'], DesignSpace):
    """Design space composed of mixtures of ingredients.

    Parameters
    ----------
    name: str
        the name of the design space
    description: str
        the description of the design space
    formulation_descriptor: FormulationDescriptor
        descriptor used to store formulations sampled from the design space
    ingredients: Set[str]
        set of ingredient names that can be used in a formulation
    constraints: Set[IngredientConstraint]
        set of constraints that restricts formulations sampled from the space.
        This must include an
        :class:`~io.citrine.informatics.constraints.ingredient_count_constraint.IngredientCountConstraint`
        with maximum count of 32 or fewer.
    labels: Optional[Mapping[str, Set[str]]]
        map from a label to each ingredient that should given that label
        when it's included in a formulation, e.g., ``{'solvent': {'water', 'alcohol'}}``
    resolution: float, optional
        Minimum increment used to specify ingredient quantities.
        Default is 0.0001.

    """

    formulation_descriptor = properties.Object(
        FormulationDescriptor,
        'data.instance.formulation_descriptor'
    )
    ingredients = properties.Set(properties.String, 'data.instance.ingredients')
    labels = properties.Optional(properties.Mapping(
        properties.String,
        properties.Set(properties.String)
    ), 'data.instance.labels')
    constraints = properties.Set(properties.Object(Constraint), 'data.instance.constraints')
    resolution = properties.Float('data.instance.resolution')

    typ = properties.String(
        'data.instance.type',
        default='FormulationDesignSpace',
        deserializable=False
    )

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 formulation_descriptor: FormulationDescriptor,
                 ingredients: Set[str],
                 constraints: Set[Constraint],
                 labels: Optional[Mapping[str, Set[str]]] = None,
                 resolution: float = 0.0001):
        self.name: str = name
        self.description: str = description
        self.formulation_descriptor: FormulationDescriptor = formulation_descriptor
        self.ingredients: Set[str] = ingredients
        self.constraints: Set[Constraint] = constraints
        self.labels: Optional[Mapping[str, Set[str]]] = labels
        self.resolution: float = resolution

    def __str__(self):
        return '<FormulationDesignSpace {!r}>'.format(self.name)

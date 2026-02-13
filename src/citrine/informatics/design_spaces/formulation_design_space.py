from typing import Optional

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine.informatics.constraints import Constraint
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.design_spaces.subspace import DesignSubspace

__all__ = ['FormulationDesignSpace']


class FormulationDesignSpace(Resource['FormulationDesignSpace'], DesignSubspace):
    """Design space composed of mixtures of ingredients.

    Parameters
    ----------
    name: str
        the name of the design space
    description: str
        the description of the design space
    formulation_descriptor: FormulationDescriptor
        descriptor used to store formulations sampled from the design space
    ingredients: set[str]
        set of ingredient names that can be used in a formulation
    constraints: set[IngredientConstraint]
        set of constraints that restricts formulations sampled from the space.
        This must include an
        :class:`~io.citrine.informatics.constraints.ingredient_count_constraint.IngredientCountConstraint`
        with maximum count of 32 or fewer.
    labels: Optional[dict[str, set[str]]]
        map from a label to each ingredient that should given that label
        when it's included in a formulation, e.g., ``{'solvent': {'water', 'alcohol'}}``
    resolution: float, optional
        Minimum increment used to specify ingredient quantities.
        Default is 0.0001.

    """

    formulation_descriptor = properties.Object(FormulationDescriptor, 'formulation_descriptor')
    ingredients = properties.Set(properties.String, 'ingredients')
    labels = properties.Optional(properties.Mapping(
        properties.String,
        properties.Set(properties.String)
    ), 'labels')
    constraints = properties.Set(properties.Object(Constraint), 'constraints')
    resolution = properties.Float('resolution')

    typ = properties.String('type', default='FormulationDesignSpace', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 formulation_descriptor: FormulationDescriptor,
                 ingredients: set[str],
                 constraints: set[Constraint],
                 labels: Optional[dict[str, set[str]]] = None,
                 resolution: float = 0.0001):
        self.name: str = name
        self.description: str = description
        self.formulation_descriptor: FormulationDescriptor = formulation_descriptor
        self.ingredients: set[str] = ingredients
        self.constraints: set[Constraint] = constraints
        self.labels: Optional[dict[str, set[str]]] = labels
        self.resolution: float = resolution

    def __str__(self):
        return '<FormulationDesignSpace {!r}>'.format(self.name)

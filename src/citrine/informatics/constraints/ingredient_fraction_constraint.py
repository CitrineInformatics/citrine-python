from typing import Optional

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.constraints.constraint import Constraint
from citrine.informatics.descriptors import FormulationDescriptor

__all__ = ['IngredientFractionConstraint']


class IngredientFractionConstraint(Serializable['IngredientFractionConstraint'], Constraint):
    """[ALPHA] Represents a constraint on an ingredient fraction in a formulation.

    Parameters
    ----------
    formulation_descriptor: FormulationDescriptor
        descriptor to constrain
    ingredient: str
        name of the ingredient to constrain
    min: float
        minimum ingredient value
    max: float
        maximum ingredient value
    is_required: bool, optional
        whether this ingredient is required.
        If ``True`` the ingredient must be present and its value must be within the
        specified range. if ``False`` the ingredient must be within the specified range
        if it's present in a formulation, i.e. the value can be 0 or on the range ``[min, max]``.

    """

    formulation_descriptor = properties.Object(FormulationDescriptor, 'formulation_descriptor')
    ingredient = properties.String('ingredient')
    min = properties.Optional(properties.Float, 'min')
    max = properties.Optional(properties.Float, 'max')
    is_required = properties.Boolean('is_required')
    typ = properties.String('type', default='IngredientFractionConstraint')

    def __init__(self, *,
                 formulation_descriptor: FormulationDescriptor,
                 ingredient: str,
                 min: float,
                 max: float,
                 is_required: bool = True,
                 session: Optional[Session] = None):
        self.formulation_descriptor: FormulationDescriptor = formulation_descriptor
        self.ingredient: str = ingredient
        self.min: float = min
        self.max: float = max
        self.is_required: bool = is_required
        self.session: Optional[Session] = session

    def __str__(self):
        return '<IngredientFractionConstraint {!r}::{!r}>'.format(
            self.formulation_descriptor.key,
            self.ingredient
        )

from typing import Optional

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.constraints.constraint import Constraint
from citrine.informatics.descriptors import FormulationDescriptor

__all__ = ['IngredientCountConstraint']


class IngredientCountConstraint(Serializable['IngredientCountConstraint'], Constraint):
    """[ALPHA] Represents a constraint on the total number of ingredients in a formulation.

    Parameters
    ----------
    formulation_descriptor: FormulationDescriptor
        descriptor to constrain
    min: int
        minimum ingredient count
    max: int
        maximum ingredient count
    label: Optional[str]
        Optional label to constrain.
        If specified only ingredients with the specified label will count towards the total.
        Default is ``None``; all ingredients count towards the total

    """

    formulation_descriptor = properties.Object(FormulationDescriptor, 'formulation_descriptor')
    min = properties.Integer('min')
    max = properties.Integer('max')
    label = properties.Optional(properties.String, 'label')
    typ = properties.String('type', default='IngredientCountConstraint')

    def __init__(self, *,
                 formulation_descriptor: FormulationDescriptor,
                 min: int,
                 max: int,
                 label: Optional[str] = None,
                 session: Optional[Session] = None):
        self.formulation_descriptor: FormulationDescriptor = formulation_descriptor
        self.min: int = min
        self.max: int = max
        self.label: Optional[str] = label
        self.session: Optional[Session] = session

    def __str__(self):
        return '<IngredientCountConstraint {!r}>'.format(self.formulation_descriptor.key)

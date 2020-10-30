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
    descriptor: FormulationDescriptor
        descriptor to constrain
    min: int
        minimum ingredient count
    max: int
        maximum ingredient count

    """

    descriptor = properties.Object(FormulationDescriptor, 'descriptor')
    min = properties.Optional(properties.Integer, 'min')
    max = properties.Optional(properties.Integer, 'max')
    typ = properties.String('type', default='IngredientCountConstraint')

    def __init__(self,
                 descriptor: FormulationDescriptor,
                 min: float,
                 max: float,
                 session: Optional[Session] = None):
        self.descriptor = descriptor
        self.min = min
        self.max = max
        self.session: Optional[Session] = session

    def __str__(self):
        return '<IngredientCountConstraint {!r}>'.format(self.descriptor.key)

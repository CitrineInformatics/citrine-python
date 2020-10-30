from typing import Optional

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.constraints.constraint import Constraint
from citrine.informatics.descriptors import FormulationDescriptor

__all__ = ['LabelCountConstraint']


class LabelCountConstraint(Serializable['LabelCountConstraint'], Constraint):
    """[ALPHA] A constraint on the total number of ingredients with a given label.

    Parameters
    ----------
    descriptor: FormulationDescriptor
        descriptor to constrain
    label: str
        label to constrain
    min: int
        minimum count
    max: int
        maximum count

    """

    descriptor = properties.Object(FormulationDescriptor, 'descriptor')
    label = properties.Optional(properties.String, 'label')
    min = properties.Optional(properties.Integer, 'min')
    max = properties.Optional(properties.Integer, 'max')
    typ = properties.String('type', default='LabelCountConstraint')

    def __init__(self,
                 descriptor: FormulationDescriptor,
                 label: str,
                 min: float,
                 max: float,
                 session: Optional[Session] = None):
        self.descriptor = descriptor
        self.label = label
        self.min = min
        self.max = max
        self.session: Optional[Session] = session

    def __str__(self):
        return '<LabelCountConstraint {!r}::{!r}>'.format(self.descriptor.key, self.label)

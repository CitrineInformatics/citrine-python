from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.constraints.constraint import Constraint
from citrine.informatics.descriptors import FormulationDescriptor

__all__ = ['LabelFractionConstraint']


class LabelFractionConstraint(Serializable['LabelFractionConstraint'], Constraint):
    """Represents a constraint on the total amount of ingredients with a given label.

    Parameters
    ----------
    formulation_descriptor: FormulationDescriptor
        descriptor to constrain
    label: str
        ingredient label to constrain
    min: float
        minimum value
    max: float
        maximum value
    is_required: bool, optional
        whether this ingredient is required.
        If ``True``, the label must be present and its value must be within the
        specified range. if ``False``, the label must be within the specified range only if
        it's present in the formulation, i.e., the value can be 0 or on the range ``[min, max]``.

    """

    formulation_descriptor = properties.Object(FormulationDescriptor, 'formulation_descriptor')
    label = properties.String('label')
    min = properties.Optional(properties.Float, 'min')
    max = properties.Optional(properties.Float, 'max')
    is_required = properties.Boolean('is_required')
    typ = properties.String('type', default='LabelFractionConstraint')

    def __init__(self, *,
                 formulation_descriptor: FormulationDescriptor,
                 label: str,
                 min: float,
                 max: float,
                 is_required: bool = True):
        self.formulation_descriptor: FormulationDescriptor = formulation_descriptor
        self.label: str = label
        self.min: float = min
        self.max: float = max
        self.is_required: bool = is_required

    def __str__(self):
        return '<LabelFractionConstraint {!r}::{!r}>'.format(
            self.formulation_descriptor.key,
            self.label
        )

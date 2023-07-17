from typing import Optional

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.constraints.constraint import Constraint

__all__ = ['IntegerRangeConstraint']


class IntegerRangeConstraint(Serializable['IntegerRangeConstraint'], Constraint):
    """[ALPHA] Represents an inequality constraint on an integer-valued material attribute.

    Warning: IntegerRangeConstraints are not fully supported by the Citrine Platform web interface
    and may cause unexpected issues until resolved.

    Parameters
    ----------
    descriptor_key: str
        the key corresponding to a descriptor
    lower_bound: int
        the minimum value in the range
    upper_bound: int
        the maximum value in the range
    lower_inclusive: bool
        if True, will include the lower bound value in the range (default: true)
    upper_inclusive: bool
        if True, will include the max value in the range (default: true)

    """

    descriptor_key = properties.String('descriptor_key')
    lower_bound = properties.Optional(properties.Float, 'min')
    upper_bound = properties.Optional(properties.Float, 'max')
    typ = properties.String('type', default='IntegerRange')

    def __init__(self, *,
                 descriptor_key: str,
                 lower_bound: Optional[int] = None,
                 upper_bound: Optional[int] = None):
        self.descriptor_key = descriptor_key
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __str__(self):
        return '<IntegerRangeConstraint {!r}>'.format(self.descriptor_key)

from typing import Optional

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.constraints.constraint import Constraint

__all__ = ['ScalarRangeConstraint']


class ScalarRangeConstraint(Serializable['ScalarRangeConstraint'], Constraint):
    """Represents an inequality constraint on a scalar-valued material attribute.

    Parameters
    ----------
    descriptor_key: str
        the key corresponding to a descriptor
    lower_bound: float
        the minimum value in the range
    upper_bound: float
        the maximum value in the range
    lower_inclusive: bool
        if True, will include the lower bound value in the range (default: true)
    upper_inclusive: bool
        if True, will include the max value in the range (default: true)

    """

    descriptor_key = properties.String('descriptor_key')
    lower_bound = properties.Optional(properties.Float, 'min')
    upper_bound = properties.Optional(properties.Float, 'max')
    lower_inclusive = properties.Boolean('min_inclusive')
    upper_inclusive = properties.Boolean('max_inclusive')
    typ = properties.String('type', default='ScalarRange')

    def __init__(self, *,
                 descriptor_key: str,
                 lower_bound: Optional[float] = None,
                 upper_bound: Optional[float] = None,
                 lower_inclusive: Optional[bool] = None,
                 upper_inclusive: Optional[bool] = None):
        self.descriptor_key = descriptor_key

        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

        # we have to be careful with None and boolean values
        # None or False or True -> True, so that pattern doesn't work
        self.lower_inclusive = True
        if lower_inclusive is not None:
            self.lower_inclusive = lower_inclusive

        self.upper_inclusive = True
        if upper_inclusive is not None:
            self.upper_inclusive = upper_inclusive

    def __str__(self):
        return '<ScalarRangeConstraint {!r}>'.format(self.descriptor_key)

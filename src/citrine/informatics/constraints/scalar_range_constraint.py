from typing import Optional

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.constraints.constraint import Constraint

__all__ = ['ScalarRangeConstraint']


class ScalarRangeConstraint(Serializable['ScalarRangeConstraint'], Constraint):
    """[ALPHA] Represents an inequality constraint on a scalar-valued material attribute.

    Parameters
    ----------
    descriptor_key: str
        the key corresponding to a descriptor
    min: float
        the minimum value in the range
    max: float
        the maximum value in the range
    min_inclusive: bool
        if True, will include the min value in the range
    max_inclusive: bool
        if True, will include the max value in the range

    """

    descriptor_key = properties.String('descriptor_key')
    min = properties.Optional(properties.Float, 'min')
    max = properties.Optional(properties.Float, 'max')
    min_inclusive = properties.Boolean('min_inclusive')
    max_inclusive = properties.Boolean('max_inclusive')
    typ = properties.String('type', default='ScalarRange')

    def __init__(self,
                 descriptor_key: str,
                 max: Optional[float] = None,
                 min: Optional[float] = None,
                 min_inclusive: Optional[bool] = True,
                 max_inclusive: Optional[bool] = True,
                 session: Optional[Session] = None):
        self.descriptor_key = descriptor_key
        self.max = max
        self.min = min
        self.min_inclusive = min_inclusive
        self.max_inclusive = max_inclusive
        self.session: Optional[Session] = session

    def __str__(self):
        return '<ScalarRangeConstraint {!r}>'.format(self.descriptor_key)

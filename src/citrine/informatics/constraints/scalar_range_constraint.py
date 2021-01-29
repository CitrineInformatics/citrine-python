from typing import Optional
from warnings import warn

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

    def __init__(self,
                 descriptor_key: str,
                 lower_bound: Optional[float] = None,
                 upper_bound: Optional[float] = None,
                 lower_inclusive: Optional[bool] = None,
                 upper_inclusive: Optional[bool] = None,
                 min: Optional[float] = None,
                 max: Optional[float] = None,
                 min_inclusive: Optional[bool] = None,
                 max_inclusive: Optional[bool] = None,
                 session: Optional[Session] = None):
        if lower_bound is not None and min is not None:
            raise ValueError("Both lower_bound and min were specified.  "
                             "Please only specify lower_bound.")
        if upper_bound is not None and max is not None:
            raise ValueError("Both upper_bound and max were specified.  "
                             "Please only specify upper_bound.")
        if lower_inclusive is not None and min_inclusive is not None:
            raise ValueError("Both lower_inclusive and min_inclusive were specified.  "
                             "Please only specify lower_inclusive.")
        if upper_inclusive is not None and max_inclusive is not None:
            raise ValueError("Both upper_inclusive and max_inclusive were specified.  "
                             "Please only specify upper_inclusive.")
        if min is not None or max is not None:
            msg = "The min/max arguments for ScalarRangeConstraint are deprecated.  " \
                  "Please use lower_bound/upper_bound instead."
            warn(msg, DeprecationWarning)
        if min_inclusive is not None or max_inclusive is not None:
            msg = "The min_inclusive/max_inclusive arguments for ScalarRangeConstraint " \
                  "are deprecated.  " \
                  "Please use lower_inclusive/upper_inclusive instead."
            warn(msg, DeprecationWarning)

        self.descriptor_key = descriptor_key
        self.lower_bound = lower_bound or min
        self.upper_bound = upper_bound or max

        # we have to be careful with None and boolean values
        # None or False or True -> True, so that pattern doesn't work
        self.lower_inclusive = True
        if lower_inclusive is not None:
            self.lower_inclusive = lower_inclusive
        elif min_inclusive is not None:
            self.lower_inclusive = min_inclusive

        self.upper_inclusive = True
        if upper_inclusive is not None:
            self.upper_inclusive = upper_inclusive
        elif max_inclusive is not None:
            self.upper_inclusive = max_inclusive

        self.session: Optional[Session] = session

    def __str__(self):
        return '<ScalarRangeConstraint {!r}>'.format(self.descriptor_key)

    @property
    def min(self):
        """[DEPRECATED] Alias for lower_bound."""
        warn("ScalarRangeConstraint.min is deprecated.  Please use lower_bound instead",
             DeprecationWarning)
        return self.lower_bound

    @property
    def max(self):
        """[DEPRECATED] Alias for upper_bound."""
        warn("ScalarRangeConstraint.max is deprecated.  Please use upper_bound instead",
             DeprecationWarning)
        return self.upper_bound

    @property
    def min_inclusive(self):
        """[DEPRECATED] Alias for lower_inclusive."""
        warn("ScalarRangeConstraint.min_inclusive is deprecated.  "
             "Please use lower_inclusive instead",
             DeprecationWarning)
        return self.lower_inclusive

    @property
    def max_inclusive(self):
        """[DEPRECATED] Alias for upper_inclusive."""
        warn("ScalarRangeConstraint.max_inclusive is deprecated.  "
             "Please use upper_inclusive instead",
             DeprecationWarning)
        return self.upper_inclusive

from typing import Optional

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.constraints.constraint import Constraint

__all__ = ['ScalarRangeConstraint']


class ScalarRangeConstraint(Serializable['ScalarRangeConstraint'], Constraint):
    """Constrain a real-valued property to a numeric range.

    Candidates whose predicted value for the specified
    descriptor falls outside the range receive a score of
    zero in the design execution.

    Parameters
    ----------
    descriptor_key : str
        The key of the descriptor to constrain. Must match
        a descriptor key defined in the predictor.
    lower_bound : float, optional
        Minimum allowed value. If omitted, no lower limit.
    upper_bound : float, optional
        Maximum allowed value. If omitted, no upper limit.
    lower_inclusive : bool, optional
        Whether the lower bound is inclusive (``>=``) or
        exclusive (``>``). Default: ``True`` (inclusive).
    upper_inclusive : bool, optional
        Whether the upper bound is inclusive (``<=``) or
        exclusive (``<``). Default: ``True`` (inclusive).

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

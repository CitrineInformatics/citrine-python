"""Tools for working with Constraints."""
from typing import List, Optional

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session

__all__ = ['Constraint', 'ScalarRangeConstraint', 'CategoricalConstraint']


class Constraint(PolymorphicSerializable['Constraint']):
    """[ALPHA] A Citrine Constraint places restrictions on a design space.

    Abstract type that returns the proper type given a serialized dict.

    """

    _response_key = None

    @classmethod
    def get_type(cls, data):
        """Return the subtype."""
        return {
            'ScalarRange': ScalarRangeConstraint,
            'Categorical': CategoricalConstraint
        }[data['type']]


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


class CategoricalConstraint(Serializable['CategoricalConstraint'], Constraint):
    """
    [ALPHA] A constraint on a categorical material attribute to be in a set of acceptable values.

    Parameters
    ----------
    descriptor_key: str
        the key corresponding to the associated Categorical descriptor
    acceptable_categories: list[str]
        the names of the acceptable categories to constrain to

    """

    descriptor_key = properties.String('descriptor_key')
    acceptable_categories = properties.List(properties.String(), 'acceptable_classes')
    typ = properties.String('type', default='Categorical')

    def __init__(self,
                 descriptor_key: str,
                 acceptable_categories: List[str],
                 session: Optional[Session] = None):
        self.descriptor_key = descriptor_key
        self.acceptable_categories = acceptable_categories
        self.session = session

    def __str__(self):
        return '<CategoricalConstraint {!r}>'.format(self.descriptor_key)

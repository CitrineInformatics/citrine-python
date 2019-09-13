"""Tools for working with Constraints."""
from typing import List, Optional

from citrine._session import Session
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable

__all__ = ['Constraint', 'ScalarRangeConstraint', 'CategoricalConstraint']


class Constraint(PolymorphicSerializable['Constraint']):
    """A Citrine Constraint - an abstract type."""

    _response_key = None

    @classmethod
    def get_type(cls, data):
        """Return the subtype."""
        return {
            'ScalarRange': ScalarRangeConstraint,
            'Categorical': CategoricalConstraint
        }[data['type']]


class ScalarRangeConstraint(Serializable['ScalarRangeConstraint'], Constraint):
    """A Citrine ScalarRangeConstraint."""

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
    """A Citrine CategoricalConstraint."""

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

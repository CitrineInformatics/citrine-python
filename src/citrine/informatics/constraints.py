"""Tools for working with Constraints."""
from typing import Optional

from citrine._session import Session
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable


class Constraint(PolymorphicSerializable['Constraint']):
    """A Citrine Constraint - an abstract type."""

    _response_key = None

    @classmethod
    def get_type(cls, data):
        """Return the only currently implemented subtype."""
        return ScalarRangeConstraint


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

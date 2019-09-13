"""Tools for working with Objectives."""
from typing import Optional

from citrine._session import Session
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable


__all__ = ['Objective', 'ScalarMaxObjective', 'ScalarMinObjective']


class Objective(PolymorphicSerializable['Objective']):
    """A Citrine Objective - an abstract type."""

    _response_key = None

    @classmethod
    def get_type(cls, data):
        """Return the subtype."""
        return {
            'ScalarMax': ScalarMaxObjective,
            'ScalarMin': ScalarMinObjective
        }[data['type']]


class ScalarMaxObjective(Serializable['ScalarMaxObjective'], Objective):
    """A Citrine ScalarMaxObjective."""

    descriptor_key = properties.String('descriptor_key')
    lower_bound = properties.Optional(properties.Float, 'lower_bound')
    upper_bound = properties.Optional(properties.Float, 'upper_bound')
    typ = properties.String('type', default='ScalarMax')

    def __init__(self,
                 descriptor_key: str,
                 lower_bound: Optional[float] = None,
                 upper_bound: Optional[float] = None,
                 session: Optional[Session] = None):
        self.descriptor_key = descriptor_key
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.session: Optional[Session] = session

    def __str__(self):
        return '<ScalarMaxObjective {!r}>'.format(self.descriptor_key)


class ScalarMinObjective(Serializable['ScalarMinObjective'], Objective):
    """A Citrine ScalarMinObjective."""

    descriptor_key = properties.String('descriptor_key')
    lower_bound = properties.Optional(properties.Float, 'lower_bound')
    upper_bound = properties.Optional(properties.Float, 'upper_bound')
    typ = properties.String('type', default='ScalarMin')

    def __init__(self,
                 descriptor_key: str,
                 lower_bound: Optional[float] = None,
                 upper_bound: Optional[float] = None,
                 session: Optional[Session] = None):
        self.descriptor_key = descriptor_key
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.session: Optional[Session] = session

    def __str__(self):
        return '<ScalarMinObjective {!r}>'.format(self.descriptor_key)

"""Tools for working with Objectives."""
from typing import Optional

from citrine._session import Session
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable


__all__ = ['Objective', 'ScalarMaxObjective', 'ScalarMinObjective']


class Objective(PolymorphicSerializable['Objective']):
    """
    [ALPHA] A Citrine Objective describes a goal for a score associated with a single descriptor.

    Abstract type that returns the proper type given a serialized dict.


    """

    _response_key = None

    @classmethod
    def get_type(cls, data):
        """Return the subtype."""
        return {
            'ScalarMax': ScalarMaxObjective,
            'ScalarMin': ScalarMinObjective
        }[data['type']]


class ScalarMaxObjective(Serializable['ScalarMaxObjective'], Objective):
    """
    [ALPHA] Simple single-response maximization objective with optional bounds.

    Parameters
    ----------
    descriptor_key: str
        the key from which to pull the values
    lower_bound: float
        the lower bound on the space, e.g. 0 for a non-negative property
    upper_bound: float
        the upper bound on the space, e.g. 0 for a non-positive property

    """

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
    """
    [ALPHA] Simple single-response minimization objective with optional bounds.

    Parameters
    ----------
    descriptor_key: str
        the key from which to pull the values
    lower_bound: float
        the lower bound on the space, e.g. 0 for a non-negative property
    upper_bound: float
        the upper bound on the space, e.g. 0 for a non-positive property

    """

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

"""Tools for working with Objectives."""
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable


__all__ = ['Objective', 'ScalarMaxObjective', 'ScalarMinObjective']


class Objective(PolymorphicSerializable['Objective']):
    """
    An Objective describes a goal for a score associated with a single descriptor.

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
    Simple single-response maximization objective with optional bounds.

    Parameters
    ----------
    descriptor_key: str
        the key from which to pull the values

    """

    descriptor_key = properties.String('descriptor_key')
    typ = properties.String('type', default='ScalarMax')

    def __init__(self, descriptor_key: str):
        self.descriptor_key = descriptor_key

    def __str__(self):
        return '<ScalarMaxObjective {!r}>'.format(self.descriptor_key)


class ScalarMinObjective(Serializable['ScalarMinObjective'], Objective):
    """
    Simple single-response minimization objective with optional bounds.

    Parameters
    ----------
    descriptor_key: str
        the key from which to pull the values

    """

    descriptor_key = properties.String('descriptor_key')
    typ = properties.String('type', default='ScalarMin')

    def __init__(self, descriptor_key: str):
        self.descriptor_key = descriptor_key

    def __str__(self):
        return '<ScalarMinObjective {!r}>'.format(self.descriptor_key)

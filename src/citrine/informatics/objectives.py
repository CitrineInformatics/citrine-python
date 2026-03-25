"""Objectives define optimization goals for design executions.

An Objective specifies what property to optimize and in which
direction. Objectives are passed to :class:`~citrine.informatics.scores.Score`
instances to define the optimization strategy.

"""
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable


__all__ = ['Objective', 'ScalarMaxObjective', 'ScalarMinObjective']


class Objective(PolymorphicSerializable['Objective']):
    """Base class for optimization objectives.

    An Objective ties a scoring direction (maximize or minimize)
    to a specific descriptor key. Use :class:`ScalarMaxObjective`
    to maximize a property or :class:`ScalarMinObjective` to
    minimize it.

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
    """Maximize a real-valued material property.

    The design execution will prefer candidates with higher
    predicted values for the specified descriptor.

    Parameters
    ----------
    descriptor_key : str
        The key of the descriptor to maximize. Must match a
        descriptor key defined in the predictor's outputs
        (e.g. ``'Tensile Strength'``).

    """

    descriptor_key = properties.String('descriptor_key')
    typ = properties.String('type', default='ScalarMax')

    def __init__(self, descriptor_key: str):
        self.descriptor_key = descriptor_key

    def __str__(self):
        return '<ScalarMaxObjective {!r}>'.format(self.descriptor_key)


class ScalarMinObjective(Serializable['ScalarMinObjective'], Objective):
    """Minimize a real-valued material property.

    The design execution will prefer candidates with lower
    predicted values for the specified descriptor.

    Parameters
    ----------
    descriptor_key : str
        The key of the descriptor to minimize. Must match a
        descriptor key defined in the predictor's outputs
        (e.g. ``'Cost'``).

    """

    descriptor_key = properties.String('descriptor_key')
    typ = properties.String('type', default='ScalarMin')

    def __init__(self, descriptor_key: str):
        self.descriptor_key = descriptor_key

    def __str__(self):
        return '<ScalarMinObjective {!r}>'.format(self.descriptor_key)

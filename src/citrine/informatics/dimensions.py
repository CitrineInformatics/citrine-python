"""Tools for working with Dimensions."""
from typing import Optional, Type, List

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.descriptors import Descriptor, RealDescriptor, IntegerDescriptor

__all__ = ['Dimension', 'ContinuousDimension', 'IntegerDimension', 'EnumeratedDimension']


class Dimension(PolymorphicSerializable['Dimension']):
    """A Dimension describes the values that a quantity can take in the context of a design space.

    Abstract type that returns the proper type given a serialized dict.

    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            'ContinuousDimension': ContinuousDimension,
            'IntegerDimension': IntegerDimension,
            'EnumeratedDimension': EnumeratedDimension
        }[data['type']]


class ContinuousDimension(Serializable['ContinuousDimension'], Dimension):
    """A continuous, real-valued dimension.

    Parameters
    ----------
    descriptor: RealDescriptor
        a descriptor of the single dimension
    lower_bound: float
        inclusive lower bound
    upper_bound: float
        inclusive upper bound

    """

    descriptor = properties.Object(RealDescriptor, 'descriptor')
    lower_bound = properties.Float('lower_bound')
    upper_bound = properties.Float('upper_bound')
    typ = properties.String('type', default='ContinuousDimension', deserializable=False)

    def __init__(self,
                 descriptor: RealDescriptor, *,
                 lower_bound: Optional[float] = None,
                 upper_bound: Optional[float] = None):
        self.descriptor: RealDescriptor = descriptor
        self.lower_bound = lower_bound if lower_bound is not None else descriptor.lower_bound
        self.upper_bound = upper_bound if upper_bound is not None else descriptor.upper_bound


class IntegerDimension(Serializable['IntegerDimension'], Dimension):
    """An integer-valued dimension with inclusive lower and upper bounds.

    Parameters
    ----------
    descriptor: IntegerDescriptor
        a descriptor of the single dimension
    lower_bound: int
        inclusive lower bound
    upper_bound: int
        inclusive upper bound

    """

    descriptor = properties.Object(IntegerDescriptor, 'descriptor')
    lower_bound = properties.Integer('lower_bound')
    upper_bound = properties.Integer('upper_bound')
    typ = properties.String('type', default='IntegerDimension', deserializable=False)

    def __init__(self,
                 descriptor: IntegerDescriptor, *,
                 lower_bound: Optional[int] = None,
                 upper_bound: Optional[int] = None):
        self.descriptor: IntegerDescriptor = descriptor
        self.lower_bound = lower_bound if lower_bound is not None else descriptor.lower_bound
        self.upper_bound = upper_bound if upper_bound is not None else descriptor.upper_bound


class EnumeratedDimension(Serializable['EnumeratedDimension'], Dimension):
    """A finite, enumerated dimension.

    Parameters
    ----------
    descriptor: Descriptor
        a descriptor of the single dimension
    values: list[str]
        list of values that can be parsed by the descriptor

    """

    descriptor = properties.Object(Descriptor, 'descriptor')
    values = properties.List(properties.String(), 'list')
    typ = properties.String('type', default='EnumeratedDimension', deserializable=False)

    def __init__(self,
                 descriptor: Descriptor, *,
                 values: List[str]):
        self.descriptor: Descriptor = descriptor
        self.values: List[str] = values

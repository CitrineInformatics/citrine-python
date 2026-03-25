"""Dimensions define the search space for design executions.

Each dimension specifies the range of values that a single
descriptor can take during candidate generation. Dimensions
are assembled into a
:class:`~citrine.informatics.design_spaces.DataSourceDesignSpace`
to define the full search space.

"""
from typing import Optional, Type, List

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.descriptors import Descriptor, RealDescriptor, IntegerDescriptor

__all__ = ['Dimension', 'ContinuousDimension', 'IntegerDimension', 'EnumeratedDimension']


class Dimension(PolymorphicSerializable['Dimension']):
    """Base class for design space dimensions.

    A Dimension restricts one descriptor to a specific range
    of values. Use the concrete subclasses:

    * :class:`ContinuousDimension` — real-valued range
    * :class:`IntegerDimension` — integer range
    * :class:`EnumeratedDimension` — finite set of values

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
    """A continuous, real-valued dimension with inclusive bounds.

    If bounds are not specified, they default to the
    descriptor's own lower and upper bounds.

    Parameters
    ----------
    descriptor : RealDescriptor
        The descriptor this dimension applies to.
    lower_bound : float, optional
        Inclusive lower bound for candidate values. Defaults
        to the descriptor's ``lower_bound``.
    upper_bound : float, optional
        Inclusive upper bound for candidate values. Defaults
        to the descriptor's ``upper_bound``.

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
    """An integer-valued dimension with inclusive bounds.

    If bounds are not specified, they default to the
    descriptor's own lower and upper bounds.

    Parameters
    ----------
    descriptor : IntegerDescriptor
        The descriptor this dimension applies to.
    lower_bound : int, optional
        Inclusive lower bound. Defaults to the descriptor's
        ``lower_bound``.
    upper_bound : int, optional
        Inclusive upper bound. Defaults to the descriptor's
        ``upper_bound``.

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
    """A dimension defined by a finite set of allowed values.

    Use this for categorical descriptors or when you want to
    restrict a continuous descriptor to specific discrete
    values (e.g. only certain temperatures).

    Parameters
    ----------
    descriptor : Descriptor
        The descriptor this dimension applies to.
    values : list[str]
        Allowed values as strings. Each string must be
        parseable by the descriptor (e.g. valid categories
        for a CategoricalDescriptor).

    """

    descriptor = properties.Object(Descriptor, 'descriptor')
    values = properties.List(properties.String(), 'list')
    typ = properties.String('type', default='EnumeratedDimension', deserializable=False)

    def __init__(self,
                 descriptor: Descriptor, *,
                 values: List[str]):
        self.descriptor: Descriptor = descriptor
        self.values: List[str] = values

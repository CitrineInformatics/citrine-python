"""Definitions for GemdQuery objects, and their sub-objects."""
from typing import List, Type

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties

__all__ = ['AllRealFilter', 'AllIntegerFilter', 'NominalCategoricalFilter']


class PropertyFilterType(PolymorphicSerializable):
    """Abstract concept of a criteria to apply when searching for materials."""

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        classes: List[Type[PropertyFilterType]] = [
            NominalCategoricalFilter,
            AllRealFilter, AllIntegerFilter
        ]
        return {klass.typ: klass for klass in classes}[data['type']]


class AllRealFilter(Serializable['AllRealFilter'], PropertyFilterType):
    """
    Filter for any real value that fits certain constraints.

    Parameters
    ----------
    lower: str
        The lower bound on this filter range.
    upper: str
        The upper bound on this filter range.
    unit: str
        The units associated with the floating point values for this filter.

    """

    lower = properties.Float('lower')
    upper = properties.Float('upper')
    unit = properties.String('unit')
    typ = properties.String('type', default="all_real_filter", deserializable=False)


class AllIntegerFilter(Serializable['AllIntegerFilter'], PropertyFilterType):
    """
    Filter for any integer value that fits certain constraints.

    Parameters
    ----------
    lower: str
        The lower bound on this filter range.
    upper: str
        The upper bound on this filter range.

    """

    lower = properties.Float('lower')
    upper = properties.Float('upper')
    typ = properties.String('type', default="all_integer_filter", deserializable=False)


class NominalCategoricalFilter(Serializable['NominalCategoricalFilter'], PropertyFilterType):
    """
    Filter based upon a fixed list of Categorical Values.

    Parameters
    ----------
    categories: Set[str]
        Which categorical values match.

    """

    categories = properties.Set(properties.String, 'categories')
    typ = properties.String('type', default="nominal_categorical_filter", deserializable=False)

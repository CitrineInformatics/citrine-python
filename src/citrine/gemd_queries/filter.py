"""Definitions for GemdQuery objects, and their sub-objects."""
from typing import List, Type

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties

__all__ = ['PropertyFilterType',
           'RealFilter', 'IntegerFilter',
           'MaterialClassification', 'TextSearchType',
           ]


class RealFilter(Serializable['RealFilter']):
    """
    A general filter for Real/Continuous Values.

    Parameters
    ----------
    unit: str
        The units associated with the floating point values for this filter.
    lower_filter: str
        The lower bound on this filter range.
    upper_filter: str
        The upper bound on this filter range.
    lower_is_inclusive: bool
        Whether the lower bound value included in the valid range.
    upper_is_inclusive: bool
        Whether the upper bound value included in the valid range.

    """

    unit = properties.String('unit')
    lower_filter = properties.Optional(properties.Float, 'lower_filter')
    upper_filter = properties.Optional(properties.Float, 'upper_filter')
    lower_is_inclusive = properties.Boolean('lower_is_inclusive')
    upper_is_inclusive = properties.Boolean('upper_is_inclusive')


class IntegerFilter(Serializable['IntegerFilter']):
    """
    A general filter for Integer/Discrete Values.

    Parameters
    ----------
    lower_filter: str
        The lower bound on this filter range.
    upper_filter: str
        The upper bound on this filter range.
    lower_is_inclusive: bool
        Whether the lower bound value included in the valid range.
    upper_is_inclusive: bool
        Whether the upper bound value included in the valid range.

    """

    lower_filter = properties.Optional(properties.Float, 'lower_filter')
    upper_filter = properties.Optional(properties.Float, 'upper_filter')
    lower_is_inclusive = properties.Boolean('lower_is_inclusive')
    upper_is_inclusive = properties.Boolean('upper_is_inclusive')


class MaterialClassification(BaseEnumeration):
    """A classification based on where in a Material History you find a Material."""

    ATOMIC_INGREDIENT = "atomic_ingredient"
    INTERMEDIATE_INGREDIENT = "intermediate_ingredient"
    TERMINAL_MATERIAL = "terminal_material"


class TextSearchType(BaseEnumeration):
    """The style of text search to run."""

    EXACT = "exact"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    SUBSTRING = "substring"


class PropertyFilterType(PolymorphicSerializable):
    """Abstract concept of a criteria to apply when searching for materials."""

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        classes: List[Type[PropertyFilterType]] = [
            NominalCategoricalFilter,
            NominalRealFilter, NormalRealFilter, UniformRealFilter,
            NominalIntegerFilter, UniformIntegerFilter,
            AllRealFilter, AllIntegerFilter
        ]
        return {klass.typ: klass for klass in classes}[data['type']]


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


class NominalRealFilter(Serializable['NominalRealFilter'], PropertyFilterType):
    """
    Filter for Nominal Reals that fit certain constraints.

    Parameters
    ----------
    values: Set[RealFilter]
        What value filter to use.

    """

    values = properties.Object(RealFilter, 'values')
    typ = properties.String('type', default="nominal_real_filter", deserializable=False)


class NormalRealFilter(Serializable['NormalRealFilter'], PropertyFilterType):
    """
    Filter for Normal Reals that fit certain constraints.

    Parameters
    ----------
    values: Set[RealFilter]
        What value filter to use.

    """

    values = properties.Object(RealFilter, 'values')
    typ = properties.String('type', default="normal_real_filter", deserializable=False)


class UniformRealFilter(Serializable['UniformRealFilter'], PropertyFilterType):
    """
    Filter for Uniform Reals that fit certain constraints.

    Parameters
    ----------
    values: Set[RealFilter]
        What value filter to use.

    """

    values = properties.Object(RealFilter, 'values')
    typ = properties.String('type', default="uniform_real_filter", deserializable=False)


class NominalIntegerFilter(Serializable['NominalIntegerFilter'], PropertyFilterType):
    """
    Filter for Nominal Integers that fit certain constraints.

    Parameters
    ----------
    values: Set[IntegerFilter]
        What value filter to use.

    """

    values = properties.Object(IntegerFilter, 'values')
    typ = properties.String('type', default="nominal_integer_filter", deserializable=False)


class UniformIntegerFilter(Serializable['UniformIntegerFilter'], PropertyFilterType):
    """
    Filter for Uniform Integers that fit certain constraints.

    Parameters
    ----------
    values: Set[IntegerFilter]
        What value filter to use.

    """

    values = properties.Object(IntegerFilter, 'values')
    typ = properties.String('type', default="uniform_integer_filter", deserializable=False)


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
    unit = properties.String('units')
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

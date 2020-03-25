"""Tools for working with Descriptors."""
from typing import Type, Optional, List  # noqa: F401

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class Descriptor(PolymorphicSerializable['Descriptor']):
    """[ALPHA] A Citrine Descriptor describes the range of values that a quantity can take on.

    Abstract type that returns the proper type given a serialized dict.

    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "Real": RealDescriptor,
            "Inorganic": InorganicDescriptor,
            "Categorical": CategoricalDescriptor
        }[data["type"]]


class RealDescriptor(Serializable['RealDescriptor'], Descriptor):
    """[ALPHA] A descriptor to hold real-valued numbers.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor
    lower_bound: float
        inclusive lower bound for valid real values
    upper_bound: float
        inclusive upper bound for valid real values

    """

    key = properties.String('descriptor_key')
    lower_bound = properties.Float('lower_bound')
    upper_bound = properties.Float('upper_bound')
    units = properties.Optional(properties.String, 'units', default='')
    typ = properties.String('type', default='Real', deserializable=False)

    def __eq__(self, other):
        try:
            attrs = ["key", "lower_bound", "upper_bound", "units", "typ"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except Exception:
            return False

    def __init__(self,
                 key: str,
                 lower_bound: float,
                 upper_bound: float,
                 units: str = ''):
        self.key: str = key
        self.lower_bound: float = lower_bound
        self.upper_bound: float = upper_bound
        self.units: Optional[str] = units


class InorganicDescriptor(Serializable['InorganicDescriptor'], Descriptor):
    """[ALPHA] Captures domain-specific context about the chemical formula for an inorganic compound.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor
    threshold: float
        the threshold for valid chemical formulae. Users can think of this as a level of tolerance
        for typos and/or loss in interpreting a string input as a parseable chemical formula.

    """

    key = properties.String('descriptor_key')
    threshold = properties.Float('threshold')
    typ = properties.String('type', default='Inorganic', deserializable=False)

    def __eq__(self, other):
        try:
            attrs = ["key", "typ"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except Exception:
            return False

    def __init__(self, key: str, threshold: float = 1.0):
        self.key: str = key
        self.threshold = threshold


class CategoricalDescriptor(Serializable['CategoricalDescriptor'], Descriptor):
    """[ALPHA] A descriptor to hold categorical variables.

    An exhaustive list of categorical values may be supplied.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor
    categories: list[str]
        possible categories for this descriptor

    """

    key = properties.String('descriptor_key')
    typ = properties.String('type', default='Categorical', deserializable=False)
    categories = properties.List(properties.String, 'descriptor_values')

    def __eq__(self, other):
        try:
            attrs = ["key", "typ"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ]) and set(self.categories) == set(self.categories + other.categories)
        except Exception:
            return False

    def __init__(self, key: str, categories: List[str]):
        self.key: str = key
        self.categories: List[str] = categories

"""Tools for working with Descriptors."""
from typing import Type, Optional, List  # noqa: F401

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class Descriptor(PolymorphicSerializable['Descriptor']):
    """An abstract descriptor type."""

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "Real": RealDescriptor,
            "Inorganic": InorganicDescriptor,
            "Categorical": CategoricalDescriptor
        }[data["type"]]


class RealDescriptor(Serializable['RealDescriptor'], Descriptor):
    """A real descriptor."""

    key = properties.String('descriptor_key')
    lower_bound = properties.Float('lower_bound')
    upper_bound = properties.Float('upper_bound')
    units = properties.Optional(properties.String, 'units', default='')
    type = properties.String('type', default='Real', deserializable=False)

    def __eq__(self, other):
        try:
            attrs = ["key", "lower_bound", "upper_bound", "units", "type"]
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
    """A real descriptor."""

    key = properties.String('descriptor_key')
    threshold = properties.Float('threshold')
    type = properties.String('type', default='Inorganic', deserializable=False)

    def __eq__(self, other):
        try:
            attrs = ["key", "type"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except Exception:
            return False

    def __init__(self, key: str, threshold: float = 1.0):
        self.key: str = key
        self.threshold = threshold


class CategoricalDescriptor(Serializable['CategoricalDescriptor'], Descriptor):
    """A categorical descriptor."""

    key = properties.String('descriptor_key')
    type = properties.String('type', default='Categorical', deserializable=False)
    categories = properties.List(properties.String, 'descriptor_values')

    def __eq__(self, other):
        try:
            attrs = ["key", "type"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ]) and set(self.categories) == set(self.categories + other.categories)
        except Exception:
            return False

    def __init__(self, key: str, categories: List[str]):
        self.key: str = key
        self.categories: List[str] = categories

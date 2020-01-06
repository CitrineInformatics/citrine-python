"""Tools for working with Descriptors."""
from typing import Type, Optional, List  # noqa: F401

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class Variable(PolymorphicSerializable['Variable']):
    """A variable that can be assigned values present in material histories

    Abstract type that returns the proper type given a serialized dict.
    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "root_info": RootInfo
        }[data["type"]]


class RootInfo(Serializable['RootInfo'], Variable):
    """Metadata from the root of the material history.

    Parameters
    ----------
    short_name: str
        a short human-readable name to use when referencing the variable
    output_name: list[str]
        sequence of column headers
    field: str
        name of the field to assign the variable to
    """

    short_name = properties.String('short_name')
    output_name = properties.List(properties.String, 'output_name')
    field = properties.String('field')
    type = properties.String('type', default="root_info", deserializable=False)

    def __eq__(self, other):
        try:
            attrs = ["short_name", "output_name", "field"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except Exception:
            return False

    def __init__(self,
                 short_name: str,
                 output_name: List[str],
                 field: str):
        self.short_name = short_name
        self.output_name = output_name
        self.field = field

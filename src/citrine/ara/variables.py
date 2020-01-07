"""Variable definitions for Ara"""
from typing import Type, Optional, List  # noqa: F401
from abc import abstractmethod

from taurus.entity.link_by_uid import LinkByUID

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class Variable(PolymorphicSerializable['Variable']):
    """A variable that can be assigned values present in material histories.

    Abstract type that returns the proper type given a serialized dict.
    """

    @abstractmethod
    def attrs(self) -> List[str]:
        pass  # pragma: no cover

    def __eq__(self, other):
        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in self.attrs()
            ])
        except AttributeError:
            return False

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        types: List[Type[Serializable]] = [
            RootInfo, AttributeByTemplate
        ]
        return next(x for x in types if x.type == data["type"])


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

    def attrs(self) -> List[str]:
        return ["short_name", "output_name", "field", "type"]

    def __init__(self,
                 short_name: str,
                 output_name: List[str],
                 field: str):
        self.short_name = short_name
        self.output_name = output_name
        self.field = field


class AttributeByTemplate(Serializable['AttributeByTemplate'], Variable):
    """Attribute marked by an attribute template.

    Parameters
    ----------
    short_name: str
        a short human-readable name to use when referencing the variable
    output_name: list[str]
        sequence of column headers
    template: LinkByUID
        attribute template that identifies the attribute to assign to the variable

    """

    short_name = properties.String('short_name')
    output_name = properties.List(properties.String, 'output_name')
    template = properties.Object(LinkByUID, 'template')
    type = properties.String('type', default="attribute_by_template", deserializable=False)

    def attrs(self) -> List[str]:
        return ["short_name", "output_name", "template", "type"]

    def __init__(self,
                 short_name: str,
                 output_name: List[str],
                 template: LinkByUID):
        self.short_name = short_name
        self.output_name = output_name
        self.template = template

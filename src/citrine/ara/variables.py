"""Variable definitions for Ara."""
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
    def _attrs(self) -> List[str]:
        pass  # pragma: no cover

    def __eq__(self, other):
        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in self._attrs()
            ])
        except AttributeError:
            return False

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        if "type" not in data:
            raise ValueError("Can only get types from dicts with a 'type' key")
        types: List[Type[Serializable]] = [
            RootInfo, AttributeByTemplate
        ]
        res = next((x for x in types if x.typ == data["type"]), None)
        if res is None:
            raise ValueError("Unrecognized type: {}".format(data["type"]))
        return res


class RootInfo(Serializable['RootInfo'], Variable):
    """Metadata from the root of the material history.

    Parameters
    ----------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    field: str
        name of the field to assign the variable to

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    field = properties.String('field')
    typ = properties.String('type', default="root_info", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "field", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 field: str):
        self.name = name
        self.headers = headers
        self.field = field


class AttributeByTemplate(Serializable['AttributeByTemplate'], Variable):
    """Attribute marked by an attribute template.

    Parameters
    ----------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    template: LinkByUID
        attribute template that identifies the attribute to assign to the variable

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    template = properties.Object(LinkByUID, 'template')
    typ = properties.String('type', default="attribute_by_template", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "template", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 template: LinkByUID):
        self.name = name
        self.headers = headers
        self.template = template

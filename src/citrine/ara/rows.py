"""Variable definitions for Ara"""
from typing import Type, Optional, List  # noqa: F401
from abc import abstractmethod

from taurus.entity.link_by_uid import LinkByUID

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class Row(PolymorphicSerializable['Row']):
    """A rule for defining rows in an Ara table.

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
            MaterialRunByTemplate
        ]
        return next(x for x in types if x.type == data["type"])


class MaterialRunByTemplate(Serializable['MaterialRunByTemplate'], Row):
    """Rows rooted in MaterialRuns, marked by their template.

    Parameters
    ----------
    templates: list[LinkByUID]
        templates of materials to include

    """

    templates = properties.List(properties.Object(LinkByUID), "templates")
    type = properties.String('type', default="material_run_by_template", deserializable=False)

    def attrs(self) -> List[str]:
        return ["templates", "type"]

    def __init__(self,
                 templates: List[LinkByUID]):
        self.templates = templates


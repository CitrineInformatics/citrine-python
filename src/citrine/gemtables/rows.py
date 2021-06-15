"""Row definitions for GEM Tables."""
from typing import Type, List, Set
from abc import abstractmethod

from gemd.entity.link_by_uid import LinkByUID

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class Row(PolymorphicSerializable['Row']):
    """[ALPHA] A rule for defining rows in a GEM Table.

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
            MaterialRunByTemplate
        ]
        res = next((x for x in types if x.typ == data["type"]), None)
        if res is None:
            raise ValueError("Unrecognized type: {}".format(data["type"]))
        return res


class MaterialRunByTemplate(Serializable['MaterialRunByTemplate'], Row):
    """[ALPHA] Rows corresponding to MaterialRuns, marked by their template.

    Parameters
    ----------
    templates: list[LinkByUID]
        templates of materials to include
    tags: Set[str]
        optional list of tags for filtering. Terminal materials containing any of those
        tags are going to be included.

    """

    templates = properties.List(properties.Object(LinkByUID), "templates")
    typ = properties.String('type', default="material_run_by_template", deserializable=False)
    tags = properties.Optional(properties.Set(properties.String), "tags")

    def _attrs(self) -> List[str]:
        return ["templates", "typ", "tags"]

    def __init__(self, *,
                 templates: List[LinkByUID],
                 tags: Set[str] = None):
        self.templates = templates
        self.tags = tags

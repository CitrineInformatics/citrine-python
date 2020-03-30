"""Top-level class for all object template objects and collections thereof."""
from abc import abstractmethod
from typing import Type

from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import ResourceType
from citrine.resources.templates import Template, TemplateCollection


class ObjectTemplate(Template):
    """
    An abstract object template object.

    ObjectTemplate must be extended along with `Resource`
    """


class ObjectTemplateCollection(TemplateCollection[ResourceType]):
    """A collection of one kind of object template object."""

    @classmethod
    @abstractmethod
    def get_type(cls) -> Type[Serializable]:
        """Return the resource type in the collection."""

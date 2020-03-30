"""Top-level class for all attribute template objects and collections thereof."""
from abc import abstractmethod
from typing import Type

from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import ResourceType
from citrine.resources.templates import Template, TemplateCollection


class AttributeTemplate(Template):
    """
    An abstract attribute template object.

    AttributeTemplate must be extended along with `Resource`
    """


class AttributeTemplateCollection(TemplateCollection[ResourceType]):
    """A collection of one kind of attribute template object."""

    @classmethod
    @abstractmethod
    def get_type(cls) -> Type[Serializable]:
        """Return the resource type in the collection."""

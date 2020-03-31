"""Top-level class for all object template objects and collections thereof."""
from abc import ABC

from citrine.resources.data_concepts import ResourceType
from citrine.resources.templates import Template, TemplateCollection


class ObjectTemplate(Template, ABC):
    """
    An abstract object template object.

    ObjectTemplate must be extended along with `Resource`
    """


class ObjectTemplateCollection(TemplateCollection[ResourceType], ABC):
    """A collection of one kind of object template object."""

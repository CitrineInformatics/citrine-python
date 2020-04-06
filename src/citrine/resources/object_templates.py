"""Top-level class for all object template objects and collections thereof."""
from abc import ABC
from typing import TypeVar

from citrine.resources.templates import Template, TemplateCollection


class ObjectTemplate(Template, ABC):
    """
    An abstract object template object.

    ObjectTemplate must be extended along with `Resource`
    """


ObjectTemplateResourceType = TypeVar("ObjectTemplateResourceType", bound="ObjectTemplate")


class ObjectTemplateCollection(TemplateCollection[ObjectTemplateResourceType], ABC):
    """A collection of one kind of object template object."""

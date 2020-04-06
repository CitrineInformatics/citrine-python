"""Top-level class for all attribute template objects and collections thereof."""
from abc import ABC
from typing import TypeVar

from citrine.resources.templates import Template, TemplateCollection


class AttributeTemplate(Template, ABC):
    """
    An abstract attribute template object.

    AttributeTemplate must be extended along with `Resource`
    """


AttributeTemplateResourceType = TypeVar("AttributeTemplateResourceType", bound="AttributeTemplate")


class AttributeTemplateCollection(TemplateCollection[AttributeTemplateResourceType]):
    """A collection of one kind of attribute template object."""

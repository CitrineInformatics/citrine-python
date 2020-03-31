"""Top-level class for all attribute template objects and collections thereof."""
from abc import ABC

from citrine.resources.data_concepts import ResourceType
from citrine.resources.templates import Template, TemplateCollection


class AttributeTemplate(Template, ABC):
    """
    An abstract attribute template object.

    AttributeTemplate must be extended along with `Resource`
    """


class AttributeTemplateCollection(TemplateCollection[ResourceType]):
    """A collection of one kind of attribute template object."""

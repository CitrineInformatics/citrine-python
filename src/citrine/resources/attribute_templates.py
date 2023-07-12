"""Top-level class for all attribute template objects and collections thereof."""
from abc import ABC
from typing import TypeVar

from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Object
from gemd.entity.template.attribute_template import AttributeTemplate as GEMDAttributeTemplate
from gemd.entity.bounds.base_bounds import BaseBounds
from citrine.resources.templates import Template, TemplateCollection


class AttributeTemplate(Template, GEMDAttributeTemplate, ABC):
    """
    An abstract attribute template object.

    AttributeTemplate must be extended along with `Resource`
    """

    name = String('name')
    description = PropertyOptional(String(), 'description')
    bounds = Object(BaseBounds, 'bounds', override=True)


AttributeTemplateResourceType = TypeVar("AttributeTemplateResourceType", bound="AttributeTemplate")


class AttributeTemplateCollection(TemplateCollection[AttributeTemplateResourceType]):
    """A collection of one kind of attribute template object."""

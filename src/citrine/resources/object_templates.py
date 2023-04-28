"""Top-level class for all object template objects and collections thereof."""
from abc import ABC
from typing import TypeVar

from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String
from citrine.resources.templates import Template, TemplateCollection
from gemd.entity.template.base_template import BaseTemplate as GEMDTemplate


class ObjectTemplate(Template, GEMDTemplate, ABC):
    """
    An abstract object template object.

    ObjectTemplate must be extended along with `Resource`
    """

    name = String('name')
    description = PropertyOptional(String(), 'description')


ObjectTemplateResourceType = TypeVar("ObjectTemplateResourceType", bound="ObjectTemplate")


class ObjectTemplateCollection(TemplateCollection[ObjectTemplateResourceType], ABC):
    """A collection of one kind of object template object."""

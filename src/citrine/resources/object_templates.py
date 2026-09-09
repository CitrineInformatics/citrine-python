"""Top-level class for all object template objects and collections thereof."""

from abc import ABC
from typing import TypeVar

from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.template.base_template import BaseTemplate as GEMDTemplate

from citrine._serialization.properties import (
    LinkOrElse,
    Object,
    Optional,
    Serializable,
    SpecifiedMixedList,
    String,
    Union,
)
from citrine.resources.templates import Template, TemplateCollection


def _attr_tuple(tempate_class: Serializable) -> Serializable:
    tuple_form = SpecifiedMixedList([LinkOrElse(tempate_class), Optional(Object(BaseBounds))])
    return Union([LinkOrElse(tempate_class), tuple_form])


class ObjectTemplate(Template, GEMDTemplate, ABC):
    """
    An abstract object template object.

    ObjectTemplate must be extended along with `Resource`
    """

    name = String("name")
    description = Optional(String(), "description")


ObjectTemplateResourceType = TypeVar("ObjectTemplateResourceType", bound="ObjectTemplate")


class ObjectTemplateCollection(TemplateCollection[ObjectTemplateResourceType], ABC):
    """A collection of one kind of object template object."""

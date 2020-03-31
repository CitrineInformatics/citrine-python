"""Top-level class for all template objects and collections thereof."""
from abc import ABC
from typing import TypeVar

from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection


class Template(DataConcepts, ABC):
    """
    An abstract template object.

    Template must be extended along with `Resource`
    """


TemplateResourceType = TypeVar("TemplateResourceType", bound="Template")


class TemplateCollection(DataConceptsCollection[TemplateResourceType], ABC):
    """A collection of one kind of template object."""

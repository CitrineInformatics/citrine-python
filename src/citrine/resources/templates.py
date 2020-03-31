"""Top-level class for all template objects and collections thereof."""
from abc import ABC

from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection, ResourceType


class Template(DataConcepts, ABC):
    """
    An abstract template object.

    Template must be extended along with `Resource`
    """


class TemplateCollection(DataConceptsCollection[ResourceType], ABC):
    """A collection of one kind of template object."""

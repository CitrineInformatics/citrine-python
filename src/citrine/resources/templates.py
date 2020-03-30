"""Top-level class for all template objects and collections thereof."""
from abc import abstractmethod
from typing import Type

from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection, ResourceType


class Template(DataConcepts):
    """
    An abstract template object.

    Template must be extended along with `Resource`
    """


class TemplateCollection(DataConceptsCollection[ResourceType]):
    """A collection of one kind of template object."""

    @classmethod
    @abstractmethod
    def get_type(cls) -> Type[Serializable]:
        """Return the resource type in the collection."""

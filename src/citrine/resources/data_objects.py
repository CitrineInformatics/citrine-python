"""Top-level class for all data object (i.e. spec and run) objects and collections thereof."""
from abc import abstractmethod
from typing import Type

from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection, ResourceType


class DataObject(DataConcepts):
    """
    An abstract data object object.

    DataObject must be extended along with `Resource`
    """


class DataObjectCollection(DataConceptsCollection[ResourceType]):
    """A collection of one kind of data object object."""

    @classmethod
    @abstractmethod
    def get_type(cls) -> Type[Serializable]:
        """Return the resource type in the collection."""

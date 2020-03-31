"""Top-level class for all data object (i.e. spec and run) objects and collections thereof."""
from abc import ABC

from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection, ResourceType


class DataObject(DataConcepts, ABC):
    """
    An abstract data object object.

    DataObject must be extended along with `Resource`
    """


class DataObjectCollection(DataConceptsCollection[ResourceType], ABC):
    """A collection of one kind of data object object."""

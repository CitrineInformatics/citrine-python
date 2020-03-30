"""Top-level class for all object run objects and collections thereof."""
from abc import abstractmethod
from typing import Type

from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import ResourceType
from citrine.resources.data_objects import DataObject, DataObjectCollection


class ObjectRun(DataObject):
    """
    An abstract object run object.

    ObjectRun must be extended along with `Resource`
    """


class ObjectRunCollection(DataObjectCollection[ResourceType]):
    """A collection of one kind of object run object."""

    @classmethod
    @abstractmethod
    def get_type(cls) -> Type[Serializable]:
        """Return the resource type in the collection."""

"""Top-level class for all object spec objects and collections thereof."""
from abc import abstractmethod
from typing import Type

from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import ResourceType
from citrine.resources.data_objects import DataObject, DataObjectCollection


class ObjectSpec(DataObject):
    """
    An abstract object spec object.

    ObjectSpec must be extended along with `Resource`
    """


class ObjectSpecCollection(DataObjectCollection[ResourceType]):
    """A collection of one kind of object spec object."""

    @classmethod
    @abstractmethod
    def get_type(cls) -> Type[Serializable]:
        """Return the resource type in the collection."""

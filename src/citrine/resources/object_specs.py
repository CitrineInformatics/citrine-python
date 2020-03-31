"""Top-level class for all object spec objects and collections thereof."""
from abc import ABC
from typing import TypeVar

from citrine.resources.data_objects import DataObject, DataObjectCollection


class ObjectSpec(DataObject, ABC):
    """
    An abstract object spec object.

    ObjectSpec must be extended along with `Resource`
    """


ObjectSpecResourceType = TypeVar("ObjectSpecResourceType", bound="ObjectSpec")


class ObjectSpecCollection(DataObjectCollection[ObjectSpecResourceType], ABC):
    """A collection of one kind of object spec object."""

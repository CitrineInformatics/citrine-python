"""Top-level class for all object run objects and collections thereof."""
from abc import ABC
from typing import TypeVar

from citrine.resources.data_objects import DataObject, DataObjectCollection
from gemd.entity.object.has_spec import HasSpec


class ObjectRun(DataObject, HasSpec, ABC):
    """
    An abstract object run object.

    ObjectRun must be extended along with `Resource`
    """


ObjectRunResourceType = TypeVar("ObjectRunResourceType", bound="ObjectRun")


class ObjectRunCollection(DataObjectCollection[ObjectRunResourceType], ABC):
    """A collection of one kind of object run object."""

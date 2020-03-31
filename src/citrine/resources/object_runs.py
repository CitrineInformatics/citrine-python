"""Top-level class for all object run objects and collections thereof."""
from abc import ABC

from citrine.resources.data_concepts import ResourceType
from citrine.resources.data_objects import DataObject, DataObjectCollection


class ObjectRun(DataObject, ABC):
    """
    An abstract object run object.

    ObjectRun must be extended along with `Resource`
    """


class ObjectRunCollection(DataObjectCollection[ResourceType], ABC):
    """A collection of one kind of object run object."""

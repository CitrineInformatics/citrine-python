from typing import Generic, TypeVar, Type
from abc import abstractmethod
from citrine._serialization.serializable import Serializable


SelfType = TypeVar('SelfType', bound='Resource')


class PolymorphicSerializable(Generic[SelfType]):
    """A Wrapper class for Polymorphic deserialization of Serializable objects."""

    @classmethod
    @abstractmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Get the underlying type based on given data."""

    @classmethod
    def build(cls, data: dict) -> SelfType:
        """Build the underlying type."""
        subtype = cls.get_type(data)
        return subtype.build(data)

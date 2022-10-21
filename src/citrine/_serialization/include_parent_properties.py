from typing import TypeVar

from citrine._serialization.serializable import Serializable

Self = TypeVar('Self', bound='Serializable')


class IncludeParentProperties(Serializable[Self]):
    # Calling Serializable.build() only populates the fields from the class itself and its
    # immediate parent. In order to include properties from the grandparent, the parent must be
    # deserialized, then merged with the results of the child's deserialization.
    @classmethod
    def build_with_parent(cls, data: dict, base_cls) -> Self:
        resource = super().build(data)

        from citrine._serialization import properties
        metadata_properties = properties.Object(base_cls).deserialize(data)

        resource.__dict__.update(metadata_properties.__dict__)
        return resource

    # This is required to allow deserialization to create an instance to read the properties.
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

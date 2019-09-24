from typing import Generic, TypeVar


Self = TypeVar('Self', bound='Serializable')


class Serializable(Generic[Self]):
    """A Serializable object."""

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        """Run data modification before building."""
        return data

    @classmethod
    def build(cls, data: dict) -> Self:
        """Build an instance of this object from given data."""
        from citrine._serialization import properties
        pre_built = cls._pre_build(data)
        return properties.Object(cls).deserialize(pre_built)

    def dump(self) -> dict:
        """Dump this instance."""
        from citrine._serialization import properties
        serialized = properties.Object(type(self)).serialize(self)
        return self._post_dump(serialized)

    def _post_dump(self, data: dict) -> dict:
        """Run data modification after dumping."""
        return data

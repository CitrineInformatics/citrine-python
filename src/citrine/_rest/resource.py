from typing import TypeVar, Optional  # noqa: F401
from citrine._serialization.serializable import Serializable

Self = TypeVar('Self', bound='Resource')


class Resource(Serializable[Self]):
    """Abstract class for representing individual REST resource."""

    _path_template: str = NotImplemented
    _response_key: Optional[str] = None

    def resource_type(self) -> str:
        """Get the access control resource type of this resource."""
        return self.__class__.__name__.upper()

    def as_entity_dict(self) -> dict:
        """Return an access control entity representation of this resource."""
        return {
            "type": self.resource_type(),
            "id": str(self.uid)
        }

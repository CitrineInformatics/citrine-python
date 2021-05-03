from typing import TypeVar, Optional  # noqa: F401
from citrine._serialization.serializable import Serializable
from gemd.enumeration.base_enumeration import BaseEnumeration


class ResourceTypeEnum(BaseEnumeration):
    """The type of the resource; used for modifying access permissions.

    * PROJECT is a Project
    * DATASET is a Dataset
    * MODULE is a Module: a Predictor, Design Space, or Processor
    * USER is a user
    * TABLE is a GemTable
    * TABLE_DEFINITION is a TableConfig

    """

    PROJECT = "PROJECT"
    DATASET = "DATASET"
    MODULE = "MODULE"
    USER = "USER"
    TABLE = "TABLE"
    TABLE_DEFINITION = "TABLE_DEFINITION"


Self = TypeVar('Self', bound='Resource')


class Resource(Serializable[Self]):
    """Abstract class for representing individual REST resource."""

    _path_template: str = NotImplemented
    _response_key: Optional[str] = None

    def resource_type(self) -> ResourceTypeEnum:
        """Get the access control resource type of this resource."""
        raise NotImplementedError

    def as_entity_dict(self) -> dict:
        """Return an access control entity representation of this resource."""
        return {
            "type": self.resource_type().value,
            "id": str(self.uid)
        }

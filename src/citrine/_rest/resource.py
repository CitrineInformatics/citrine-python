from typing import TypeVar, Optional, Union
from uuid import UUID

from citrine._serialization.serializable import Serializable
from citrine._serialization import properties
from gemd.enumeration.base_enumeration import BaseEnumeration


class ResourceTypeEnum(BaseEnumeration):
    """The type of the resource; used for modifying access controls.

    * TEAM is a Team
    * PROJECT is a Project
    * DATASET is a Dataset
    * MODULE is a Module: a Predictor or Design Space
    * USER is a user
    * TABLE is a GemTable
    * TABLE_DEFINITION is a TableConfig

    """

    TEAM = "TEAM"
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
    _resource_type: ResourceTypeEnum = NotImplemented

    def access_control_dict(self) -> dict:
        """Return an access control entity representation of this resource. Internal use only."""
        return {
            "type": self._resource_type.value,
            "id": str(self.uid)
        }


class ResourceRef(Serializable['ResourceRef']):
    """A reference to a resource by UID."""

    # json key 'module_uid' is a legacy of when this object was only used for modules
    uid = properties.UUID('module_uid')

    def __init__(self, uid: Union[UUID, str]):
        self.uid = uid


class PredictorRef(Serializable['PredictorRef']):
    """A reference to a resource by UID."""

    uid = properties.UUID('predictor_id')
    version = properties.Optional(
        properties.Union([properties.Integer(), properties.String()]),
        'predictor_version'
    )

    def __init__(self, uid: Union[UUID, str], version: Optional[Union[int, str]] = None):
        self.uid = uid
        self.version = version

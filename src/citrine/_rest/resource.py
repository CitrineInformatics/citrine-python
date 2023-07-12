from typing import TypeVar, Optional, Union
from uuid import UUID

from citrine._serialization.serializable import Serializable
from citrine._serialization import properties
from gemd.entity.dict_serializable import DictSerializable
from gemd.enumeration.base_enumeration import BaseEnumeration
from gemd.util import make_index, substitute_objects


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


GEMDSelf = TypeVar('GEMDSelf', bound='GEMDResource')


class GEMDResource(Resource[GEMDSelf]):
    """A reference to a resource by UID."""

    @classmethod
    def build(cls, data: dict) -> GEMDSelf:
        """Convert a raw, nested dictionary into Objects."""
        if "context" in data and len(data) == 2:
            def _inflate(x):
                return DictSerializable.class_mapping[x["type"]].build(x)
            key = next(k for k in data if k != "context")
            idx = make_index([_inflate(x) for x in data["context"] + [data[key]]])
            lst = [idx[k] for k in idx]
            substitute_objects(lst, idx, inplace=True)

            root = _inflate(data[key])
            if root in idx:  # It was a link
                return idx[root]
            else:  # It was an object, but it won't be densely linked
                return idx[root.to_link()]
        else:
            if data.get("type") is not None:
                if not issubclass(cls, DictSerializable.class_mapping.get(data.get("type"))):
                    raise ValueError(f"{cls.__name__} passed a {data.get('type')} dictionary.")
            return super().build(data)

    def as_dict(self) -> dict:
        """
        Dump to a dictionary (useful for interoperability with gemd).

        Because of the _key mapping in Property, __dict__'s keys are fundamentally different
        between gemd.entity.dict_serializable and this class.  This means we can't just use gemd's
        as_dict for comparisons.
        """
        result = dict()
        for name, property_ in properties.Object(type(self)).fields.items():
            if property_.serializable:
                result[property_.serialization_path] = getattr(self, name, None)
        return result


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

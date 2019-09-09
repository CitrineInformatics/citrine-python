from typing import TypeVar, Optional  # noqa: F401
from citrine._serialization.serializable import Serializable

Self = TypeVar('Self', bound='Resource')


class Resource(Serializable[Self]):
    """Abstract class for representing individual REST resource."""

    _path_template: str = NotImplemented
    _response_key: Optional[str] = None

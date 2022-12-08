from typing import TypeVar, Union

from citrine._serialization.serializable import Serializable
from citrine._serialization import properties

from gemd.enumeration.base_enumeration import BaseEnumeration


StatusDetailType = TypeVar('StatusDetailType', bound='StatusDetail')


class StatusLevelEnum(BaseEnumeration):
    """The level of the status message."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    UNKOWN = "Unknown"


class StatusDetail(Serializable[StatusDetailType]):
    """A status message and its level."""

    msg = properties.String("msg")
    level = properties.String("level")

    def __init__(self, *, msg: str, level: Union[str, StatusLevelEnum]):
        if not isinstance(level, StatusLevelEnum):
            level = StatusLevelEnum.get_enum(level)

        self.msg = msg
        self.level = level.value

    def __str__(self):
        return f"[{self.level.upper()}] {self.msg}"  # pragma: no cover

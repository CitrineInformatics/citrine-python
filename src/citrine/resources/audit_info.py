from gemd.entity.dict_serializable import DictSerializable

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable


class AuditInfo(Serializable, DictSerializable, typ="audit_info"):
    """Model that holds audit metadata. AuditInfo objects should not be created by the user."""

    created_by = properties.Optional(properties.UUID, "created_by")
    """:UUID | None: ID of the user who created the object"""
    created_at = properties.Optional(properties.Datetime, "created_at")
    """:datetime | None: Time, in ms since epoch, at which the object was created"""
    updated_by = properties.Optional(properties.UUID, "updated_by")
    """:UUID | None: ID of the user who most recently updated the object"""
    updated_at = properties.Optional(properties.Datetime, "updated_at")
    """:datetime | None: Time, in ms since epoch, at which the object was
    most recently updated"""

    def __init__(self):
        pass  # pragma: no cover

    def __repr__(self):
        return (
            f"Created by: {self.created_by!r}\n"
            f"Created at: {self.created_at!r}\n"
            f"Updated by: {self.updated_by!r}\n"
            f"Updated at: {self.updated_at!r}"
        )

    def __str__(self):
        create_str = f"Created by user {self.created_by} at time {self.created_at}"
        if self.updated_by is not None or self.updated_at is not None:
            update_str = f"\nUpdated by user {self.updated_by} at time {self.updated_at}"
        else:
            update_str = ""
        return create_str + update_str

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()

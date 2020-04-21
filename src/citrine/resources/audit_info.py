from typing import Optional
from uuid import UUID
from datetime import datetime

from citrine._serialization.serializable import Serializable
from citrine._serialization import properties
from gemd.entity.dict_serializable import DictSerializable


class AuditInfo(Serializable, DictSerializable):
    """
    Model that holds audit metadata. AuditInfo objects should not be created by the user.

    Parameters
    ----------
    created_by: Optional[UUID]
        ID of the user who created the object
    created_at: Optional[Datetime]
        Time, in ms since epoch, at which the object was created
    updated_by: Optional[UUID]
        ID of the user who most recently updated the object
    updated_at: Optional[Datetime]
        Time, in ms since epoch, at which the object was most recently updated

    """

    created_by = properties.Optional(properties.UUID, 'created_by')
    created_at = properties.Optional(properties.Datetime, 'created_at')
    updated_by = properties.Optional(properties.UUID, 'updated_by')
    updated_at = properties.Optional(properties.Datetime, 'updated_at')

    def __init__(self, created_by: Optional[UUID], created_at: Optional[datetime],
                 updated_by: Optional[UUID] = None, updated_at: Optional[datetime] = None):
        self.created_by = created_by
        self.created_at = created_at
        self.updated_by = updated_by
        self.updated_at = updated_at

    def __repr__(self):
        return 'Created by: {!r}\nCreated at: {!r}\nUpdated by: {!r}\nUpdated at: {!r}'.format(
            self.created_by, self.created_at, self.updated_by, self.updated_at
        )

    def __str__(self):
        create_str = 'Created by user {} at time {}'.format(
            self.created_by, self.created_at)
        if self.updated_by is not None or self.updated_at is not None:
            update_str = '\nUpdated by user {} at time {}'.format(
                self.updated_by, self.updated_at)
        else:
            update_str = ''
        return create_str + update_str

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()

    def as_dict(self):
        """Return the object as a dictionary."""
        return self.dump()

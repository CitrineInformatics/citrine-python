from deprecation import deprecated
from typing import List

from citrine._serialization import properties


class PredictorMetadata:
    """Abstract class for representing metadata for Predictors."""

    created_by = properties.Optional(properties.UUID, 'metadata.creation.user', serializable=False)
    """:Optional[UUID]: id of the user who created the resource"""
    create_time = properties.Optional(properties.Datetime, 'metadata.creation.time',
                                      serializable=False)
    """:Optional[datetime]: date and time at which the resource was created"""

    updated_by = properties.Optional(properties.UUID, 'metadata.last_update.user',
                                     serializable=False)
    """:Optional[UUID]: id of the user who most recently updated the resource,
    if it has been updated"""
    update_time = properties.Optional(properties.Datetime, 'metadata.last_update.time',
                                      serializable=False)
    """:Optional[datetime]: date and time at which the resource was most recently updated,
    if it has been updated"""

    archived_by = properties.Optional(properties.UUID, 'metadata.archived.user',
                                      serializable=False)
    """:Optional[UUID]: id of the user who archived the resource, if it has been archived"""
    archive_time = properties.Optional(properties.Datetime, 'metadata.archiveed.time',
                                       serializable=False)
    """:Optional[datetime]: date and time at which the resource was archived,
    if it has been archived"""

    status = properties.Optional(properties.String(), 'metadata.status', serializable=False)
    """:Optional[str]: short description of the resource's status"""
    status_info = properties.Optional(properties.List(properties.String()), 'metadata.status_info',
                                      serializable=False)

    # Due to the way object construction is done at present, __init__ is not executed on Resource
    # objects, so initializing _archived doesn't work.
    _archived = properties.Optional(properties.Boolean(), '', default=None, serializable=False,
                                    deserializable=False)

    @property
    def is_archived(self):
        """:bool: whether the resource is archived (hidden but not deleted)."""
        return self.archived_by is not None

    @property
    @deprecated(deprecated_in="1.30.0", removed_in="2.0.0",
                details="Please use the 'is_archived' property instead.'")
    def archived(self):
        """[DEPRECATED] whether the resource is archived."""
        return self.is_archived

    @archived.setter
    @deprecated(deprecated_in="1.30.0", removed_in="2.0.0",
                details="Please use archive() and restore() on PredictorCollection instead.")
    def archived(self, value):
        self._archived = value

    @property
    @deprecated(deprecated_in="1.25.0", removed_in="2.0.0")
    def experimental(self) -> bool:
        """[DEPRECATED] whether the execution is experimental (newer, less well-tested)."""  # noqa - insisting this docstring is a signature
        return False

    @property
    @deprecated(deprecated_in="1.25.0", removed_in="2.0.0")
    def experimental_reasons(self) -> List[str]:
        """[DEPRECATED] human-readable reasons why the execution is experimental."""
        return []

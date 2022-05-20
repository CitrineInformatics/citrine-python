from deprecation import deprecated
from typing import List, TypeVar

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties


Self = TypeVar('Self', bound='Resource')


# This class is the base type for the new module endpoints. Currently, it only covers predictors,
# but should be applicable for others as they're written.
class EngineResource(Resource[Self]):
    """Base resource for predictors, including metadata representation."""

    created_by = properties.Optional(properties.UUID, 'metadata.created.user', serializable=False)
    """:Optional[UUID]: id of the user who created the resource"""
    create_time = properties.Optional(properties.Datetime, 'metadata.created.time',
                                      serializable=False)
    """:Optional[datetime]: date and time at which the resource was created"""

    updated_by = properties.Optional(properties.UUID, 'metadata.updated.user',
                                     serializable=False)
    """:Optional[UUID]: id of the user who most recently updated the resource,
    if it has been updated"""
    update_time = properties.Optional(properties.Datetime, 'metadata.updated.time',
                                      serializable=False)
    """:Optional[datetime]: date and time at which the resource was most recently updated,
    if it has been updated"""

    archived_by = properties.Optional(properties.UUID, 'metadata.archived.user',
                                      serializable=False)
    """:Optional[UUID]: id of the user who archived the resource, if it has been archived"""
    archive_time = properties.Optional(properties.Datetime, 'metadata.archived.time',
                                       serializable=False)
    """:Optional[datetime]: date and time at which the resource was archived,
    if it has been archived"""

    status = properties.Optional(properties.String(), 'metadata.status.name', serializable=False)
    """:Optional[str]: short description of the resource's status"""
    status_info = properties.Optional(properties.List(properties.String()), 'metadata.status.info',
                                      serializable=False)

    # Due to the way object construction is done at present, __init__ is not executed on Resource
    # objects, so initializing _archived doesn't work.
    _archived = properties.Optional(properties.Boolean(), '', default=None, serializable=False,
                                    deserializable=False)

    _resource_type = ResourceTypeEnum.MODULE

    @property
    def is_archived(self):
        """:bool: whether the resource is archived (hidden but not deleted)."""
        return self.archived_by is not None

    @property
    @deprecated(deprecated_in="1.31.0", removed_in="2.0.0",
                details="Please use the 'is_archived' property instead.'")
    def archived(self):
        """[DEPRECATED] whether the resource is archived."""
        return self.is_archived

    @archived.setter
    @deprecated(deprecated_in="1.31.0", removed_in="2.0.0",
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

    def _post_dump(self, data: dict) -> dict:
        # Only the data portion of an entity is sent to the server.
        data = data["data"]

        # Currently, name and description exists on both the data envelope and the config.
        data["instance"]["name"] = data["name"]
        data["instance"]["description"] = data["description"]
        return data

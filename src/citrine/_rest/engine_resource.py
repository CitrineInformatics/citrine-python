from typing import TypeVar

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._serialization.include_parent_properties import IncludeParentProperties
from citrine.resources.status_detail import StatusDetail

Self = TypeVar('Self', bound='Resource')


# This class is the base type for the new module endpoints which do not support versions. If/once
# they support versioning, they should be switched to inherit from VersionedEngineResource.
class EngineResource(Resource[Self]):
    """Base resource for metadata from stand-alone AI Engine modules."""

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
    status_detail = properties.List(properties.Object(StatusDetail), 'metadata.status.detail',
                                    default=[], serializable=False)
    """:List[StatusDetail]: a list of structured status info, containing the message and level"""

    _resource_type = ResourceTypeEnum.MODULE

    def _post_dump(self, data: dict) -> dict:
        # Only the data portion of an entity is sent to the server.
        data = data["data"]

        # Currently, name and description exists on both the data envelope and the config.
        data["instance"]["name"] = data["name"]
        data["instance"]["description"] = data["description"]
        return data


class VersionedEngineResource(EngineResource[Self], IncludeParentProperties[Self]):
    """Base resource for metadata from stand-alone AI Engine modules which support versioning."""

    """:Integer: The version number of the resource."""
    version = properties.Optional(properties.Integer, 'metadata.version', serializable=False)

    """:Boolean: The draft status of the resource."""
    draft = properties.Optional(properties.Boolean, 'metadata.draft', serializable=False)

    @classmethod
    def build(cls, data: dict):
        """Build an instance of this object from given data."""
        return super().build_with_parent(data, __class__)

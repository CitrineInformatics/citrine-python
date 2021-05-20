from citrine._serialization import properties


class AIResourceMetadata():
    """Abstract class for representing common metadata for Resources."""

    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    """:Optional[UUID]: id of the user who created the resource"""
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)
    """:Optional[datetime]: date and time at which the resource was created"""

    updated_by = properties.Optional(properties.UUID, 'updated_by', serializable=False)
    """:Optional[UUID]: id of the user who most recently updated the resource,
    if it has been updated"""
    update_time = properties.Optional(properties.Datetime, 'update_time', serializable=False)
    """:Optional[datetime]: date and time at which the resource was most recently updated,
    if it has been updated"""

    archived = properties.Boolean('archived', default=False)
    """:bool: whether the resource is archived (hidden but not deleted)"""
    archived_by = properties.Optional(properties.UUID, 'archived_by', serializable=False)
    """:Optional[UUID]: id of the user who archived the resource, if it has been archived"""
    archive_time = properties.Optional(properties.Datetime, 'archive_time', serializable=False)
    """:Optional[datetime]: date and time at which the resource was archived,
    if it has been archived"""

    experimental = properties.Boolean("experimental", serializable=False, default=True)
    """:bool: whether the resource is experimental (newer, less well-tested functionality)"""
    experimental_reasons = properties.Optional(
        properties.List(properties.String()),
        'experimental_reasons',
        serializable=False
    )
    """:Optional[List[str]]: human-readable reasons why the resource is experimental"""

    status = properties.Optional(properties.String(), 'status', serializable=False)
    """:Optional[str]: short description of the resource's status"""
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    """:Optional[List[str]]: human-readable explanations of the status"""

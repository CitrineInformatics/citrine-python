from typing import Optional  # noqa: F401
from citrine._serialization import properties


class AIResourceMetadata():
    """Abstract class for representing common metadata for Resources."""

    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)

    updated_by = properties.Optional(properties.UUID, 'updated_by', serializable=False)
    update_time = properties.Optional(properties.Datetime, 'update_time', serializable=False)

    archived = properties.Boolean('archived', default=False)
    archived_by = properties.Optional(properties.UUID, 'archived_by', serializable=False)
    archive_time = properties.Optional(properties.Datetime, 'archive_time', serializable=False)

    experimental = properties.Boolean("experimental", serializable=False, default=True)
    experimental_reasons = properties.Optional(
        properties.List(properties.String()),
        'experimental_reasons',
        serializable=False
    )

    status = properties.Optional(properties.String(), 'status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )

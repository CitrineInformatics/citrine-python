from typing import TypeVar, Optional  # noqa: F401
from citrine._serialization.serializable import Serializable
from citrine._serialization import properties

Self = TypeVar('Self', bound='Mixin')


class Mixin():
    """Abstract class for representing individual REST Mixin."""

    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)

    updated_by = properties.Optional(properties.UUID, 'updated_by', serializable=False)
    update_time = properties.Optional(properties.Datetime, 'update_time', serializable=False)

    archived_by = properties.Optional(properties.UUID, 'archived_by', serializable=False)
    archive_time = properties.Optional(properties.Datetime, 'archive_time', serializable=False)

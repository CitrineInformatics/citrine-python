"""Tools for working with workflow resources."""
from typing import Optional
from uuid import UUID

from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._session import Session
from citrine._serialization import properties


__all__ = ['Workflow']


class Workflow(AsynchronousObject):
    """A Citrine Workflow is a collection of Modules that together accomplish some task.

    All workflows must inherit AIResourceMetadata, and hence have a ``status`` field.
    Possible statuses are INPROGRESS, SUCCEEDED, and FAILED.
    Workflows also have a ``status_description`` field with more information.

    """

    _response_key = None
    _session: Optional[Session] = None
    _in_progress_statuses = ["INPROGRESS"]
    _succeeded_statuses = ["SUCCEEDED"]
    _failed_statuses = ["FAILED"]

    project_id: Optional[UUID] = None
    """:Optional[UUID]: Unique ID of the project that contains this workflow."""
    name = properties.String('name')
    description = properties.Optional(properties.String, 'description')
    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    """:Optional[UUID]: Citrine Platform unique identifier"""

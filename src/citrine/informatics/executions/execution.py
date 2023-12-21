from abc import ABC
from typing import Optional
from uuid import UUID

from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._rest.pageable import Pageable
from citrine._rest.paginator import Paginator
from citrine._serialization import properties
from citrine._session import Session
from citrine.resources.status_detail import StatusDetail


class Execution(Pageable, AsynchronousObject, ABC):
    """A base class for execution resources.

    This class provides an abstraction for the execution resources.
    """

    _paginator: Paginator = Paginator()
    _collection_key = 'response'
    _in_progress_statuses = ["INPROGRESS"]
    _succeeded_statuses = ["SUCCEEDED"]
    _failed_statuses = ["FAILED"]
    _session: Optional[Session] = None
    project_id: Optional[UUID] = None

    uid: UUID = properties.UUID('id', serializable=False)
    """:UUID: Unique identifier of the execution"""
    status = properties.Optional(properties.String(), 'status', serializable=False)
    """:Optional[str]: short description of the execution's status"""
    status_description = properties.Optional(
        properties.String(), 'status_description', serializable=False)
    """:Optional[str]: more detailed description of the execution's status"""
    status_detail = properties.List(
        properties.Object(StatusDetail), 'status_detail', default=[], serializable=False
    )
    """:List[StatusDetail]: a list of structured status info, containing the message and level"""
    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    """:Optional[UUID]: id of the user who created the resource"""
    updated_by = properties.Optional(properties.UUID, 'updated_by', serializable=False)
    """:Optional[UUID]: id of the user who most recently updated the resource,
    if it has been updated"""
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)
    """:Optional[datetime]: date and time at which the resource was created"""
    update_time = properties.Optional(properties.Datetime, 'update_time', serializable=False)
    """:Optional[datetime]: date and time at which the resource was most recently updated,
    if it has been updated"""

    def __str__(self):
        return f'<{self.__class__.__name__} {str(self.uid)!r}>'

    def _path(self):
        raise NotImplementedError("Subclasses must implement the _path method")  # pragma: no cover

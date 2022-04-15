"""Tools for working with module resources."""
from typing import Type, Optional
from uuid import UUID

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._session import Session
from citrine._rest.asynchronous_object import AsynchronousObject

__all__ = ['Module']


class Module(PolymorphicSerializable['Module'], AsynchronousObject):
    """A Citrine Module is a reusable computational tool used to construct a workflow.

    Abstract type that returns the proper type given a serialized dict.

    All modules must inherit AIResourceMetadata, and hence have a ``status`` field.
    Possible statuses are CREATED, VALIDATING, INVALID, ERROR, and READY.

    """

    _response_key = None
    _project_id: Optional[UUID] = None
    _session: Optional[Session] = None
    _in_progress_statuses = ["VALIDATING", "CREATED"]
    _succeeded_statuses = ["READY"]
    _failed_statuses = ["INVALID", "ERROR"]

    @classmethod
    def get_type(cls, data) -> Type['Module']:
        """Return the subtype."""
        from citrine.informatics.design_spaces import DesignSpace
        from citrine.informatics.processors import Processor
        return {
            'DESIGN_SPACE': DesignSpace,
            'PROCESSOR': Processor
        }[data['module_type']].get_type(data)

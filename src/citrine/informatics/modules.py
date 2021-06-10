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

    @classmethod
    def get_type(cls, data) -> Type['Module']:
        """Return the subtype."""
        from citrine.informatics.design_spaces import DesignSpace
        from citrine.informatics.processors import Processor
        from citrine.informatics.predictors import Predictor
        return {
            'DESIGN_SPACE': DesignSpace,
            'PROCESSOR': Processor,
            'PREDICTOR': Predictor
        }[data['module_type']].get_type(data)

    def in_progress(self) -> bool:
        """Whether module validation is in progress."""
        updated_status = self._fetch_updated().status
        return updated_status == "VALIDATING" or updated_status == "CREATED"

    def succeeded(self) -> bool:
        """Whether module validation has completed successfully."""
        updated_status = self._fetch_updated().status
        return updated_status == "READY"

    def failed(self) -> bool:
        """Whether module validation has completed unsuccessfully. Does not query state."""
        updated_status = self._fetch_updated().status
        return updated_status == "INVALID" or updated_status == "ERROR"

    def _fetch_updated(self) -> 'Module':
        if self._project_id is None or self._session is None or self.uid is None:
            raise RuntimeError(f"Cannot get updated version of resource \'{self.name}\'. "
                               "Are you using an on-platform resource?")
        path = f'/projects/{self._project_id}/modules/{self.uid}'
        data = self._session.get_resource(path)
        return self.build(data)

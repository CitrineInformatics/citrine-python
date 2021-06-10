"""Tools for working with workflow resources."""
from typing import Type, Optional
from uuid import UUID

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._session import Session
from citrine._serialization import properties


__all__ = ['Workflow']


class Workflow(PolymorphicSerializable['Workflow'], AsynchronousObject):
    """A Citrine Workflow is a collection of Modules that together accomplish some task.

    Abstract type that returns the proper type given a serialized dict.

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

    @classmethod
    def get_type(cls, data) -> Type['Workflow']:
        """Return the subtype."""
        from .design_workflow import DesignWorkflow
        from .predictor_evaluation_workflow import PredictorEvaluationWorkflow
        type_dict = {
            'DESIGN_WORKFLOW': DesignWorkflow,
            'PREDICTOR_EVALUATION_WORKFLOW': PredictorEvaluationWorkflow,
        }
        typ = type_dict.get(data['module_type'])

        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid workflow type. '
                'Must be in {}.'.format(data['module_type'], type_dict.keys())
            )

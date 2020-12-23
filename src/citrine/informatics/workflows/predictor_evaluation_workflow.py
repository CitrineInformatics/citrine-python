from typing import List, Optional  # noqa
from uuid import UUID  # noqa

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session  # noqa
from citrine.informatics.predictor_evaluator import PredictorEvaluator
from citrine.informatics.workflows.workflow import Workflow
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecutionCollection

__all__ = ['PredictorEvaluationWorkflow']


class PredictorEvaluationWorkflow(Resource['PredictorEvaluationWorkflow'], Workflow):
    """A workflow that evaluations a predictor.

    Parameters
    ----------
    name: str
        name of the predictor evaluation workflow
    description: str
        the description of the predictor evaluation workflow
    evaluators: List[PredictorEvaluator]
        the list of evaluators to apply to the predictor

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('name')
    description = properties.String('description')
    evaluators = properties.List(properties.Object(PredictorEvaluator), "evaluators")
    status = properties.String('status', serializable=False)
    status_description = properties.String('status_description', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    experimental = properties.Boolean("experimental", serializable=False, default=True)
    experimental_reasons = properties.Optional(
        properties.List(properties.String()),
        'experimental_reasons',
        serializable=False
    )
    archived = properties.Boolean('archived', default=False)
    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    updated_by = properties.Optional(properties.UUID, 'updated_by', serializable=False)
    archived_by = properties.Optional(properties.UUID, 'archived_by', serializable=False)
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)
    update_time = properties.Optional(properties.Datetime, 'update_time', serializable=False)
    archive_time = properties.Optional(properties.Datetime, 'archive_time', serializable=False)
    typ = properties.String('type', default='PredictorEvaluationWorkflow', deserializable=False)

    def __init__(self, *,
                 name: str,
                 description: str = "",
                 evaluators: List[PredictorEvaluator]):
        self.name: str = name
        self.description: str = description
        self.evaluators: List[PredictorEvaluator] = evaluators
        self.session: Optional[Session] = None
        self.project_id: Optional[UUID] = None

    def __str__(self):
        return '<PredictorEvaluationWorkflow {!r}>'.format(self.name)

    @property
    def executions(self) -> PredictorEvaluationExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return PredictorEvaluationExecutionCollection(
            project_id=self.project_id, session=self.session, workflow_id=self.uid)

from typing import List, Optional
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.informatics.predictor_evaluator import PredictorEvaluator
from citrine.informatics.workflows.workflow import Workflow
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecutionCollection

__all__ = ['PredictorEvaluationWorkflow']


class PredictorEvaluationWorkflow(Resource['PredictorEvaluationWorkflow'], Workflow):
    """[ALPHA] A workflow that evaluations a predictor.

    Parameters
    ----------
    uid: str
        Unique identifier of the predictor evaluation workflow
    name: str
        name of the predictor evaluation workflow
    description: str
        the description of the predictor evaluation workflow
    evaluators: List[PredictorEvaluator]
        the list of evaluators to apply to the predictor

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('display_name')
    description = properties.String('description')
    evaluators = properties.List(properties.Object(PredictorEvaluator), "evaluators")
    status = properties.String('status', serializable=False)
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
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)
    module_type = properties.String('module_type', default='PREDICTOR_EVALUATION_WORKFLOW')
    typ = properties.String('type', default='PredictorEvaluationWorkflow', deserializable=False)

    def __init__(self, *,
                 name: str,
                 description: str = "",
                 evaluators: List[PredictorEvaluator],
                 uid: Optional[UUID] = None,
                 project_id: Optional[UUID] = None,
                 session: Session = Session()):
        self.name: str = name
        self.description: str = description
        self.evaluators: List[PredictorEvaluator] = evaluators
        self.project_id: Optional[UUID] = project_id
        self.uid: Optional[UUID] = uid
        self.session: Session = session

    def __str__(self):
        return '<PredictorEvaluationWorkflow {!r}>'.format(self.name)

    @property
    def executions(self) -> PredictorEvaluationExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return PredictorEvaluationExecutionCollection(self.project_id, self.uid, self.session)

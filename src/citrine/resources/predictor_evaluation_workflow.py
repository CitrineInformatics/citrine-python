"""Resources that represent both individual and collections of workflow executions."""
from typing import Optional, List
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.informatics.predictor_evaluator import PredictorEvaluator


class PredictorEvaluationWorkflow(Resource['PredictorEvaluationWorkflow']):
    """[ALPHA] A process for evaluating a predictor

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

    _response_key = 'WorkflowExecutions'

    uid = properties.UUID('id')
    status = properties.Optional(properties.String(), 'status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    name = properties.String('name')
    description = properties.String('description')
    evaluators = properties.List(properties.Object(PredictorEvaluator), "evaluators")

    def __init__(self, *,
                 uid: Optional[str] = None,
                 name: str,
                 description: str = "",
                 evaluators: List[PredictorEvaluator],
                 session: Optional[Session] = None,
                 ):
        self.uid: str = uid
        self.session: Session = session
        self.name = name
        self.description = description
        self.evaluators = evaluators

    def __str__(self):
        return '<PredictorEvaluationWorkflow {!r}>'.format(str(self.uid))

    def _path(self):
        return '/projects/{project_id}/workflows/{workflow_id}/executions/{execution_id}'.format(
            **{
                "project_id": self.project_id,
                "workflow_id": self.workflow_id,
                "execution_id": self.uid
            }
        )


class PredictorEvaluationWorkflowCollection(Collection[PredictorEvaluationWorkflow]):
    """[ALPHA] A collection of PredictorEvaluationWorkflows."""

    _path_template = '/projects/{project_id}/predictor-evaluation-workflows'
    _individual_key = None
    _collection_key = 'response'
    _resource = PredictorEvaluationWorkflow

    def __init__(self, *,
                 project_id: UUID,
                 session: Optional[Session] = None
                 ):
        self.project_id: UUID = project_id
        self.session: Optional[Session] = session

    def build(self, data: dict) -> PredictorEvaluationWorkflow:
        """Build an individual PredictorEvaluationExecution."""
        execution = PredictorEvaluationWorkflow.build(data)
        execution.session = self.session
        execution.project_id = self.project_id
        return execution

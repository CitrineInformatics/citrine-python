"""Resources that represent both individual and collections of workflow executions."""
from functools import lru_cache
from typing import Optional, Set
from uuid import UUID

from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult
from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session


class PredictorEvaluationExecution(Resource['PredictorEvaluationExecution']):
    """[ALPHA] The execution of a PredictorEvaluationWorkflow.

    Parameters
    ----------
    uid: str
        Unique identifier of the workflow execution
    project_id: str
        Unique identifier of the project that contains the workflow execution
    workflow_id: str
        Unique identifier of the workflow that was executed
    version_number: int
        Integer identifier that increases each time the workflow is executed.  The first execution
        has version_number = 1.

    """

    _response_key = 'WorkflowExecutions'

    uid = properties.UUID('id')
    project_id = properties.UUID('project_id', deserializable=False)
    workflow_id = properties.UUID('workflow_id', deserializable=False)
    version_number = properties.Integer("version_number")
    status = properties.Optional(properties.String(), 'status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )

    def __init__(self, *,
                 uid: Optional[str] = None,
                 version_number: Optional[int] = None,
                 project_id: Optional[str] = None,
                 workflow_id: Optional[str] = None,
                 predictor_id: Optional[str] = None,
                 metric_names: Optional[Set[str]] = None,
                 response_names: Optional[Set[str]] = None,
                 evaluator_names: Optional[Set[str]] = None,
                 session: Optional[Session] = None,
                 ):
        self.uid: str = uid
        self.version_number = version_number
        self.project_id: str = project_id
        self.workflow_id: str = workflow_id
        self.session: Session = session
        self.predictor_id: str = predictor_id
        self.metric_names: Set[str] = metric_names
        self.response_names: Set[str] = response_names
        self.evaluator_names: Set[str] = evaluator_names

    def __str__(self):
        return '<PredictorEvaluationExecution {!r}>'.format(str(self.uid))

    def _path(self):
        return '/projects/{project_id}/workflows/{workflow_id}/executions/{execution_id}'.format(
            **{
                "project_id": self.project_id,
                "workflow_id": self.workflow_id,
                "execution_id": self.uid
            }
        )

    @lru_cache
    def results(self, evaluator_name) -> PredictorEvaluationResult:
        """

        Parameters
        ----------
        evaluator_name: str
            Name of the evaluator for which to get the results

        Returns
        -------
        The evaluation result from the evaluator with the given name

        """
        params = {"evaluator_name": evaluator_name}
        return PredictorEvaluationResult.build(self.session.get_resource(self._path() + "/results", params=params))


class PredictorEvaluationExecutionCollection(Collection["PredictorEvaluationExecution"]):
    """[ALPHA] A collection of PredictorEvaluationExecutions."""

    _path_template = '/projects/{project_id}/workflows/{workflow_id}/executions'
    _individual_key = None
    _collection_key = 'response'
    _resource = PredictorEvaluationExecution

    def __init__(self, *,
                 project_id: UUID,
                 workflow_id: Optional[UUID] = None,
                 session: Optional[Session] = None
                 ):
        self.project_id: UUID = project_id
        self.workflow_id: Optional[UUID] = workflow_id
        self.session: Optional[Session] = session

    def build(self, data: dict) -> PredictorEvaluationExecution:
        """Build an individual PredictorEvaluationExecution."""
        execution = PredictorEvaluationExecution.build(data)
        execution.session = self.session
        execution.project_id = self.project_id
        if self.workflow_id is not None:
            execution.workflow_id = self.workflow_id
        return execution

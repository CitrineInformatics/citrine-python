"""Resources that represent both individual and collections of workflow executions."""
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.workflows import PredictorEvaluationWorkflow


class PredictorEvaluationWorkflowCollection(Collection[PredictorEvaluationWorkflow]):
    """[ALPHA] A collection of PredictorEvaluationWorkflows."""

    _path_template = '/projects/{project_id}/predictor-evaluation-workflows'
    _individual_key = None
    _resource = PredictorEvaluationWorkflow

    def __init__(self, project_id: UUID, session: Session):
        self.project_id: UUID = project_id
        self.session: Session = session

    def build(self, data: dict) -> PredictorEvaluationWorkflow:
        """Build an individual PredictorEvaluationExecution."""
        execution = PredictorEvaluationWorkflow.build(data)
        execution.session = self.session
        execution.project_id = self.project_id
        return execution

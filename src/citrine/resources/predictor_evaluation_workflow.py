"""Resources that represent both individual and collections of workflow executions."""
from typing import Union
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.modules import PredictorRef
from citrine.informatics.workflows import PredictorEvaluationWorkflow
from citrine.resources.response import Response


class PredictorEvaluationWorkflowCollection(Collection[PredictorEvaluationWorkflow]):
    """A collection of PredictorEvaluationWorkflows."""

    _path_template = '/projects/{project_id}/predictor-evaluation-workflows'
    _individual_key = None
    _collection_key = 'response'
    _resource = PredictorEvaluationWorkflow

    def __init__(self, project_id: UUID, session: Session):
        self.project_id: UUID = project_id
        self.session: Session = session

    def build(self, data: dict) -> PredictorEvaluationWorkflow:
        """Build an individual PredictorEvaluationExecution."""
        workflow = PredictorEvaluationWorkflow.build(data)
        workflow.session = self.session
        workflow.project_id = self.project_id
        return workflow

    def archive(self, workflow_id: UUID):
        """Archive a predictor evaluation workflow.

        Parameters
        ----------
        workflow_id: UUID
            Unique identifier of the workflow to archive

        """
        return self._put_module_ref('archive', workflow_id)

    def restore(self, workflow_id: UUID):
        """Restore a predictor evaluation workflow.

        Parameters
        ----------
        workflow_id: UUID
            Unique identifier of the workflow to restore

        """
        return self._put_module_ref('restore', workflow_id)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Predictor Evaluation Workflows cannot be deleted; they can be archived instead."""
        raise NotImplementedError(
            "Predictor Evaluation Workflows cannot be deleted; they can be archived instead.")

    def create_default(self, predictor_id: UUID) -> PredictorEvaluationWorkflow:
        """[ALPHA] Create a default predictor evaluation workflow for a predictor and execute it.

        Parameters
        ----------
        predictor_id: UUID
            Unique identifier of the predictor used to create a default workflow

        Returns
        -------
        PredictorEvaluationWorkflow
            Default workflow

        """
        url = self._get_path('default')
        ref = PredictorRef(str(predictor_id))
        data = self.session.post_resource(url, ref.dump())
        self._check_experimental(data)
        return self.build(data)

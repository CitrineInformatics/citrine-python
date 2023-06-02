"""Resources that represent both individual and collections of predictor evaluation executions."""
from functools import partial
from typing import Optional, Union, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import PredictorRef
from citrine._session import Session
from citrine._utils.functions import MigratedClassMeta, format_escaped_url
from citrine.informatics.executions import predictor_evaluation_execution
from citrine.resources.response import Response


class PredictorEvaluationExecution(predictor_evaluation_execution.PredictorEvaluationExecution,
                                   deprecated_in="2.22.1",
                                   removed_in="3.0.0",
                                   metaclass=MigratedClassMeta):
    """The execution of a PredictorEvaluationWorkflow.

    Possible statuses are INPROGRESS, SUCCEEDED, and FAILED.
    Predictor evaluation executions also have a ``status_description`` field with more information.

    """


class PredictorEvaluationExecutionCollection(Collection["PredictorEvaluationExecution"]):
    """A collection of PredictorEvaluationExecutions."""

    _path_template = '/projects/{project_id}/predictor-evaluation-executions'  # noqa
    _individual_key = None
    _collection_key = 'response'
    _resource = predictor_evaluation_execution.PredictorEvaluationExecution

    def __init__(self,
                 project_id: UUID,
                 session: Session,
                 workflow_id: Optional[UUID] = None):
        self.project_id: UUID = project_id
        self.session: Session = session
        self.workflow_id: Optional[UUID] = workflow_id

    def build(self, data: dict) -> predictor_evaluation_execution.PredictorEvaluationExecution:
        """Build an individual PredictorEvaluationExecution."""
        execution = predictor_evaluation_execution.PredictorEvaluationExecution.build(data)
        execution._session = self.session
        execution.project_id = self.project_id
        return execution

    def trigger(self,
                predictor_id: UUID,
                *,
                predictor_version: Optional[Union[int, str]] = None,
                random_state: Optional[int] = None):
        """Trigger a predictor evaluation execution against a predictor.

        Parameters
        -----------
        predictor_id: UUID
            ID of the predictor to evaluate.
        predictor_version: Union[int, str], optional
            The version of the predictor to evaluate.
        random_state: int, optional
            Seeds the evaluators' random number generator so that the results are repeatable.

        """
        if self.workflow_id is None:
            msg = "Cannot trigger a predictor evaluation execution without knowing the " \
                  "predictor evaluation workflow. Use workflow.executions.trigger instead of " \
                  "project.predictor_evaluation_executions.trigger"
            raise RuntimeError(msg)
        path = format_escaped_url(
            '/projects/{project_id}/predictor-evaluation-workflows/{workflow_id}/executions',
            project_id=self.project_id,
            workflow_id=self.workflow_id
        )

        params = dict()
        if random_state is not None:
            params["random_state"] = random_state

        payload = PredictorRef(predictor_id, predictor_version).dump()
        data = self.session.post_resource(path, payload, params=params, version='v2')

        return self.build(data)

    def register(self,
                 model: predictor_evaluation_execution.PredictorEvaluationExecution
                 ) -> predictor_evaluation_execution.PredictorEvaluationExecution:
        """Cannot register an execution."""
        raise NotImplementedError("Cannot register a PredictorEvaluationExecution.")

    def update(self,
               model: predictor_evaluation_execution.PredictorEvaluationExecution
               ) -> predictor_evaluation_execution.PredictorEvaluationExecution:
        """Cannot update an execution."""
        raise NotImplementedError("Cannot update a PredictorEvaluationExecution.")

    def archive(self, uid: Union[UUID, str]):
        """Archive a predictor evaluation execution.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the execution to archive

        """
        self._put_resource_ref('archive', uid)

    def restore(self, uid: Union[UUID, str]):
        """Restore an archived predictor evaluation execution.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the execution to restore

        """
        self._put_resource_ref('restore', uid)

    def list(self,
             *,
             per_page: int = 100,
             predictor_id: Optional[UUID] = None,
             predictor_version: Optional[Union[int, str]] = None
             ) -> Iterator[predictor_evaluation_execution.PredictorEvaluationExecution]:
        """
        Paginate over the elements of the collection.

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.
        predictor_id: uuid, optional
            list executions that targeted the predictor with this id
        predictor_version: Union[int, str], optional
            list executions that targeted the predictor with this version

        Returns
        -------
        Iterator[PredictorEvaluationExecution]
            The matching predictor evaluation executions.

        """
        params = {}
        if predictor_id is not None:
            params["predictor_id"] = str(predictor_id)
        if predictor_version is not None:
            params["predictor_version"] = predictor_version
        if self.workflow_id is not None:
            params["workflow_id"] = str(self.workflow_id)

        fetcher = partial(self._fetch_page, additional_params=params)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Predictor Evaluation Executions cannot be deleted; they can be archived instead."""
        raise NotImplementedError(
            "Predictor Evaluation Executions cannot be deleted; they can be archived instead.")

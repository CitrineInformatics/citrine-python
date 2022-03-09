"""Resources that represent both individual and collections of predictor evaluation executions."""
from functools import partial
import sys
from typing import Optional, Union, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import ResourceRef
from citrine._session import Session
from citrine._utils.functions import migrate_deprecated_argument, shadow_classes_in_module, \
    format_escaped_url
from citrine.informatics.executions import PredictorEvaluationExecution
import citrine.informatics.executions.predictor_evaluation_execution
from citrine.resources.response import Response


shadow_classes_in_module(citrine.informatics.executions.predictor_evaluation_execution,
                         sys.modules[__name__])


class PredictorEvaluationExecutionCollection(Collection["PredictorEvaluationExecution"]):
    """A collection of PredictorEvaluationExecutions."""

    _path_template = '/projects/{project_id}/predictor-evaluation-executions'  # noqa
    _individual_key = None
    _collection_key = 'response'
    _resource = PredictorEvaluationExecution

    def __init__(self,
                 project_id: UUID,
                 session: Session,
                 workflow_id: Optional[UUID] = None):
        self.project_id: UUID = project_id
        self.session: Session = session
        self.workflow_id: Optional[UUID] = workflow_id

    def build(self, data: dict) -> PredictorEvaluationExecution:
        """Build an individual PredictorEvaluationExecution."""
        execution = PredictorEvaluationExecution.build(data)
        execution._session = self.session
        execution.project_id = self.project_id
        return execution

    def trigger(self, predictor_id: UUID):
        """Trigger a predictor evaluation execution against a predictor, by id."""
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
        data = self.session.post_resource(path, ResourceRef(predictor_id).dump())
        return self.build(data)

    def register(self, model: PredictorEvaluationExecution) -> PredictorEvaluationExecution:
        """Cannot register an execution."""
        raise NotImplementedError("Cannot register a PredictorEvaluationExecution.")

    def update(self, model: PredictorEvaluationExecution) -> PredictorEvaluationExecution:
        """Cannot update an execution."""
        raise NotImplementedError("Cannot update a PredictorEvaluationExecution.")

    def archive(self, uid: Union[UUID, str] = None, execution_id: Union[UUID, str] = None):
        """Archive a predictor evaluation execution.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the execution to archive
        execution_id: Union[UUID, str]
            [DEPRECATED] please use uid instead

        """
        uid = migrate_deprecated_argument(uid, "uid", execution_id, "execution_id")
        self._put_resource_ref('archive', uid)

    def restore(self, uid: Union[UUID, str] = None, execution_id: Union[UUID, str] = None):
        """Restore an archived predictor evaluation execution.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the execution to restore
        execution_id: Union[UUID, str]
            [DEPRECATED] please use uid instead

        """
        uid = migrate_deprecated_argument(uid, "uid", execution_id, "execution_id")
        self._put_resource_ref('restore', uid)

    def list(self,
             *,
             page: Optional[int] = None,
             per_page: int = 100,
             predictor_id: Optional[UUID] = None
             ) -> Iterator[PredictorEvaluationExecution]:
        """
        Paginate over the elements of the collection.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is to read all pages and yield
            all results.  This option is deprecated.
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.
        predictor_id: uuid, optional
            list executions that targeted the predictor with this id

        Returns
        -------
        Iterator[ResourceType]
            Resources in this collection.

        """
        params = {}
        if predictor_id is not None:
            params["predictor_id"] = str(predictor_id)
        if self.workflow_id is not None:
            params["workflow_id"] = str(self.workflow_id)

        fetcher = partial(self._fetch_page, additional_params=params)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
                                        per_page=per_page)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Predictor Evaluation Executions cannot be deleted; they can be archived instead."""
        raise NotImplementedError(
            "Predictor Evaluation Executions cannot be deleted; they can be archived instead.")

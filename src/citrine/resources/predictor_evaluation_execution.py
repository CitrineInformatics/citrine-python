"""Resources that represent both individual and collections of workflow executions."""
from functools import lru_cache, partial
from typing import Optional, Iterable, Union
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.informatics.modules import ModuleRef
from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult
from citrine.resources.response import Response


class PredictorEvaluationExecution(Resource['PredictorEvaluationExecution']):
    """The execution of a PredictorEvaluationWorkflow.

    Parameters
    ----------
    uid: str
        Unique identifier of the workflow execution
    project_id: str
        Unique identifier of the project that contains the workflow execution
    workflow_id: str
        Unique identifier of the workflow that was executed

    """

    _response_key = None

    uid: UUID = properties.UUID('id', serializable=False)
    """UUID of the execution."""

    evaluator_names = properties.List(properties.String, "evaluator_names", serializable=False)
    workflow_id = properties.UUID('workflow_id', serializable=False)
    predictor_id = properties.UUID('predictor_id', serializable=False)
    status = properties.Optional(properties.String(), 'status', serializable=False)
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

    def __init__(self):
        """This shouldn't be called, but it defines members that are set elsewhere."""
        self.project_id: Optional[UUID] = None  # pragma: no cover
        self.session: Optional[Session] = None  # pragma: no cover

    def __str__(self):
        return '<PredictorEvaluationExecution {!r}>'.format(str(self.uid))

    def _path(self):
        return '/projects/{project_id}/predictor-evaluation-executions/{execution_id}' \
            .format(project_id=self.project_id,
                    workflow_id=self.workflow_id,
                    execution_id=self.uid)

    @lru_cache()
    def results(self, evaluator_name: str) -> PredictorEvaluationResult:
        """
        Get a specific evaluation result by the name of the evaluator that produced it.

        Parameters
        ----------
        evaluator_name: str
            Name of the evaluator for which to get the results

        Returns
        -------
        The evaluation result from the evaluator with the given name

        """
        params = {"evaluator_name": evaluator_name}
        resource = self.session.get_resource(self._path() + "/results", params=params)
        return PredictorEvaluationResult.build(resource)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.results(item)
        else:
            raise TypeError("Results are accessed by string names")

    def __iter__(self):
        return iter(self.evaluator_names)


class PredictorEvaluationExecutionCollection(Collection["PredictorEvaluationExecution"]):
    """A collection of PredictorEvaluationExecutions."""

    _path_template = '/projects/{project_id}/predictor-evaluation-executions'  # noqa
    _individual_key = None
    _collection_key = 'response'
    _resource = PredictorEvaluationExecution

    def __init__(self, *,
                 project_id: UUID,
                 session: Session,
                 workflow_id: Optional[UUID] = None):
        self.project_id: UUID = project_id
        self.session: Session = session
        self.workflow_id: Optional[UUID] = workflow_id

    def build(self, data: dict) -> PredictorEvaluationExecution:
        """Build an individual PredictorEvaluationExecution."""
        execution = PredictorEvaluationExecution.build(data)
        execution.session = self.session
        execution.project_id = self.project_id
        return execution

    def trigger(self, predictor_id: UUID):
        """Trigger a predictor evaluation execution against a predictor, by id."""
        path = '/projects/{project_id}/predictor-evaluation-workflows/{workflow_id}/executions' \
            .format(project_id=self.project_id, workflow_id=self.workflow_id)
        data = self.session.post_resource(path, ModuleRef(str(predictor_id)).dump())
        self._check_experimental(data)
        return self.build(data)

    def register(self, model: PredictorEvaluationExecution) -> PredictorEvaluationExecution:
        """Cannot register an execution."""
        raise NotImplementedError("Cannot register a PredictorEvaluationExecution.")

    def update(self, model: PredictorEvaluationExecution) -> PredictorEvaluationExecution:
        """Cannot update an execution."""
        raise NotImplementedError("Cannot update a PredictorEvaluationExecution.")

    def archive(self, execution_id: UUID):
        """Archive a predictor evaluation execution.

        Parameters
        ----------
        execution_id: UUID
            Unique identifier of the execution to archive

        """
        self._put_module_ref('archive', execution_id)

    def restore(self, execution_id: UUID):
        """Restore a predictor evaluation execution.

        Parameters
        ----------
        execution_id: UUID
            Unique identifier of the execution to restore

        """
        self._put_module_ref('restore', execution_id)

    def list(self,
             page: Optional[int] = None,
             per_page: int = 100,
             predictor_id: Optional[UUID] = None
             ) -> Iterable[PredictorEvaluationExecution]:
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
        Iterable[ResourceType]
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

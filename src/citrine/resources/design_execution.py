"""Resources that represent both individual and collections of workflow executions."""
from functools import partial
from typing import Optional, Iterable, Union
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.paginator import Paginator
from citrine._rest.pageable import Pageable
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.informatics.design_candidate import DesignCandidate
from citrine.resources.response import Response
from citrine.informatics.scores import Score


class DesignExecution(Resource['DesignExecution'], Pageable):
    """The execution of a DesignWorkflow.

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

    _response_key = None
    _paginator: Paginator = Paginator()
    _collection_key = 'response'

    uid: UUID = properties.UUID('id', serializable=False)
    workflow_id = properties.UUID('workflow_id', serializable=False)
    version_number = properties.Integer("version_number", serializable=False)

    status = properties.Optional(properties.String(), 'status', serializable=False)
    status_description = properties.Optional(
        properties.String(), 'status_description', serializable=False)
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
    archived = properties.Boolean('archived')
    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    updated_by = properties.Optional(properties.UUID, 'updated_by', serializable=False)
    archived_by = properties.Optional(properties.UUID, 'archived_by', serializable=False)
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)
    update_time = properties.Optional(properties.Datetime, 'update_time', serializable=False)
    archive_time = properties.Optional(properties.Datetime, 'archive_time', serializable=False)

    def __init__(self):
        """This shouldn't be called, but it defines members that are set elsewhere."""
        self.project_id: Optional[UUID] = None  # pragma: no cover
        self.session: Optional[Session] = None  # pragma: no cover

    def __str__(self):
        return '<DesignExecution {!r}>'.format(str(self.uid))

    def _path(self):
        return '/projects/{project_id}/design-workflows/{workflow_id}/executions/{execution_id}' \
            .format(project_id=self.project_id,
                    workflow_id=self.workflow_id,
                    execution_id=self.uid)

    @classmethod
    def _build_candidates(cls, subset_collection: Iterable[dict]) -> Iterable[DesignCandidate]:
        for candidate in subset_collection:
            yield DesignCandidate.build(candidate)

    def candidates(self,
                   page: Optional[int] = None,
                   per_page: int = 100,
                   ) -> Iterable[DesignCandidate]:
        """Fetch the Design Candidates for the particular execution, paginated."""
        path = self._path() + '/candidates'

        fetcher = partial(self._fetch_page, path=path)

        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_candidates,
                                        page=page,
                                        per_page=per_page)


class DesignExecutionCollection(Collection["DesignExecution"]):
    """A collection of DesignExecutions."""

    _path_template = '/projects/{project_id}/design-workflows/{workflow_id}/executions'  # noqa
    _individual_key = None
    _collection_key = 'response'
    _resource = DesignExecution

    def __init__(self, *,
                 project_id: UUID,
                 session: Session,
                 workflow_id: Optional[UUID] = None):
        self.project_id: UUID = project_id
        self.session: Session = session
        self.workflow_id: UUID = workflow_id

    def build(self, data: dict) -> DesignExecution:
        """Build an individual DesignWorkflowExecution."""
        execution = DesignExecution.build(data)
        execution.session = self.session
        execution.project_id = self.project_id
        return execution

    def trigger(self, execution_input: Score):
        """Trigger a Design Workflow execution given a score."""
        path = self._get_path()
        data = self.session.post_resource(path, {'score': execution_input.dump()})
        self._check_experimental(data)
        return self.build(data)

    def register(self, model: DesignExecution) -> DesignExecution:
        """Cannot register an execution."""
        raise NotImplementedError("Cannot register a DesignExecution.")

    def update(self, model: DesignExecution) -> DesignExecution:
        """Cannot update an execution."""
        raise NotImplementedError("Cannot update a DesignExecution.")

    def archive(self, execution_id: UUID):
        """Archive a Design Workflow execution.

        Parameters
        ----------
        execution_id: UUID
            Unique identifier of the execution to archive

        """
        raise NotImplementedError(
            "Design Executions cannot be archived")

    def restore(self, execution_id: UUID):
        """Restore a Design Workflow execution.

        Parameters
        ----------
        execution_id: UUID
            Unique identifier of the execution to restore

        """
        raise NotImplementedError(
            "Design Executions cannot be restored")

    def list(self,
             page: Optional[int] = None,
             per_page: int = 100,
             ) -> Iterable[DesignExecution]:
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
        return self._paginator.paginate(page_fetcher=self._fetch_page,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
                                        per_page=per_page)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Design Workflow Executions cannot be deleted or archived."""
        raise NotImplementedError(
            "Design Executions cannot be deleted")

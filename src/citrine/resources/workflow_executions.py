"""Resources that represent both individual and collections of workflow executions."""
from functools import partial
from typing import Optional, Iterable
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.paginator import Paginator
from citrine._rest.pageable import Pageable
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.informatics.design_candidate import DesignCandidate
from citrine.informatics.modules import ModuleRef
from citrine.informatics.scores import Score


class WorkflowExecution(Resource['WorkflowExecution'], Pageable):
    """[ALPHA] A Citrine Workflow Execution.

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
    _paginator: Paginator = Paginator()
    _collection_key = 'response'

    uid = properties.UUID('id')
    project_id = properties.UUID('project_id', deserializable=False)
    workflow_id = properties.UUID('workflow_id', deserializable=False)
    version_number = properties.Integer("version_number")

    def __init__(self,
                 uid: Optional[str] = None,
                 project_id: Optional[str] = None,
                 workflow_id: Optional[str] = None,
                 session: Optional[Session] = None,
                 version_number: Optional[int] = None,
                 ):
        self.uid: str = uid
        self.project_id: str = project_id
        self.workflow_id: str = workflow_id
        self.session: Session = session
        self.version_number = version_number

    def __str__(self):
        return '<WorkflowExecution {!r}>'.format(str(self.uid))

    def _path(self):
        return '/projects/{project_id}/workflows/{workflow_id}/executions/{execution_id}'.format(
            **{
                "project_id": self.project_id,
                "workflow_id": self.workflow_id,
                "execution_id": self.uid
            }
        )

    def status(self):
        """Get the current status of this execution."""
        response = self.session.get_resource(self._path() + "/status")
        return WorkflowExecutionStatus.build(response)

    def results(self):
        """Get the results of this execution."""
        return self.session.get_resource(self._path() + "/results")

    @classmethod
    def _build_candidates(cls, subset_collection: Iterable[dict]) -> Iterable[DesignCandidate]:
        for candidate in subset_collection:
            yield DesignCandidate.build(candidate)

    def candidates(self,
                   page: Optional[int] = None,
                   per_page: int = 100,
                   ) -> Iterable[DesignCandidate]:
        """Fetch the Design Candidates for the particular execution, paginated.

        Gets candidates from the new candidates API for a workflow executed by the old api.
        New candidates are paginated and have structured types.
        """
        path = '/projects/{p_id}/design-workflows/{w_id}/executions/{e_id}/candidates'.format(
            p_id=self.project_id,
            w_id=self.workflow_id,
            e_id=self.uid
        )

        fetcher = partial(self._fetch_page, path=path)

        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_candidates,
                                        page=page,
                                        per_page=per_page)


class WorkflowExecutionCollection(Collection[WorkflowExecution]):
    """[ALPHA] A collection of WorkflowExecutions."""

    _path_template = '/projects/{project_id}/workflows/{workflow_id}/executions'
    _individual_key = None
    _collection_key = 'response'
    _resource = WorkflowExecution

    def __init__(self, project_id: UUID, workflow_id: Optional[UUID],
                 session: Optional[Session] = None):
        self.project_id: UUID = project_id
        self.workflow_id: Optional[UUID] = workflow_id
        self.session: Optional[Session] = session

    def build(self, data: dict) -> WorkflowExecution:
        """Build an individual WorkflowExecution."""
        execution = WorkflowExecution.build(data)
        execution.session = self.session
        execution.project_id = self.project_id
        if self.workflow_id is not None:
            execution.workflow_id = self.workflow_id
        return execution

    def trigger(self, execution_input: [Score, ModuleRef]) -> WorkflowExecution:
        """Create a new workflow execution."""
        return self.register(execution_input)


class WorkflowExecutionStatus(Resource['WorkflowExecutionStatus']):
    """[ALPHA] The status for a specific workflow execution."""

    status = properties.String('status')

    def __init__(self,
                 status: str,
                 session: Optional[Session]):
        self.status = status

    @property
    def succeeded(self):
        """Determine whether or not the execution succeeded."""
        return self.status == "Succeeded"

    @property
    def in_progress(self):
        """Determine whether or not the execution is in progress."""
        return self.status == "InProgress"

    @property
    def failed(self):
        """Determine whether or not the execution failed."""
        return self.status == "Failed"

    @property
    def timed_out(self):
        """Determine whether or not the execution timed out."""
        return self.status == "TimedOut"

    def __str__(self):
        return '<WorkflowExecutionStatus {!r}>'.format(self.status)

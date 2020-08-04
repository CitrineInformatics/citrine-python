"""Resources that represent both individual and collections of workflow executions."""
from typing import Optional
from uuid import UUID

from citrine.informatics.modules import ModuleRef
from citrine.informatics.scores import Score
from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session


class WorkflowExecution(Resource['WorkflowExecution']):
    """[ALPHA] A Citrine Workflow Execution."""

    _response_key = 'WorkflowExecutions'

    uid = properties.UUID('id')
    project_id = properties.UUID('project_id', deserializable=False)
    workflow_id = properties.UUID('workflow_id', deserializable=False)

    def __init__(self,
                 uid: Optional[str] = None,
                 project_id: Optional[str] = None,
                 workflow_id: Optional[str] = None,
                 session: Optional[Session] = None):
        self.uid: str = uid
        self.project_id: str = project_id
        self.workflow_id: str = workflow_id
        self.session: Session = session

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


class WorkflowExecutionCollection(Collection[WorkflowExecution]):
    """[ALPHA] A collection of WorkflowExecutions."""

    _path_template = '/projects/{project_id}/workflows/{workflow_id}/executions'
    _individual_key = None
    _collection_key = 'response'
    _resource = WorkflowExecution

    def __init__(self, project_id: UUID, workflow_id: UUID, session: Optional[Session] = None):
        self.project_id: UUID = project_id
        self.workflow_id: UUID = workflow_id
        self.session: Optional[Session] = session

    def build(self, data: dict) -> WorkflowExecution:
        """Build an individual WorkflowExecution."""
        execution = WorkflowExecution.build(data)
        execution.session = self.session
        execution.project_id = self.project_id
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

    def __str__(self):
        return '<WorkflowExecutionStatus {!r}>'.format(self.status)

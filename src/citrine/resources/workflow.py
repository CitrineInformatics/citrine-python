"""Resources that represent both individual and collections of projects."""
from uuid import UUID
from typing import TypeVar

from citrine.informatics.workflows import Workflow, DesignWorkflow

from citrine._rest.collection import Collection
from citrine._session import Session

CreationType = TypeVar('CreationType', bound=Workflow)


class WorkflowCollection(Collection[Workflow]):
    """Represents the collection of all Workflows as well as the resources belonging to it."""

    _path_template = '/projects/{project_id}/workflows'
    _individual_key = None
    _resource = Workflow

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> Workflow:
        """Build an individual Workflow."""
        workflow = DesignWorkflow.build(data)
        workflow.session = self.session
        workflow.project_id = self.project_id
        return workflow

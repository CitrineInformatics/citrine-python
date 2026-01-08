from typing import TypeVar, Union
from uuid import UUID

from citrine._session import Session
from citrine.informatics.workflows import DesignWorkflow, Workflow
from citrine.resources.design_workflow import DesignWorkflowCollection
from tests.utils.fakes import FakeCollection

WorkflowType = TypeVar("WorkflowType", bound="Workflow")


class FakeWorkflowCollection(FakeCollection[WorkflowType]):
    def __init__(self, project_id, session: Session):
        FakeCollection.__init__(self)
        self.project_id = project_id
        self.session = session

    def register(self, workflow: WorkflowType) -> WorkflowType:
        workflow = FakeCollection.register(self, workflow)
        workflow.project_id = self.project_id
        return workflow

    def archive(self, uid: Union[UUID, str]):
        # Search for workflow via UID to ensure exists
        # If found, flip archived=True with no return
        workflow = self.get(uid)
        workflow.archived = True
        self.update(workflow)


class FakeDesignWorkflowCollection(
    FakeWorkflowCollection[DesignWorkflow], DesignWorkflowCollection
):
    pass

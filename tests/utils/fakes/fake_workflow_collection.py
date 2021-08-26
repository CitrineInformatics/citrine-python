from typing import TypeVar, Union
from uuid import uuid4, UUID

from citrine._session import Session
from citrine._utils.functions import migrate_deprecated_argument
from citrine.exceptions import BadRequest
from citrine.informatics.workflows import PredictorEvaluationWorkflow, DesignWorkflow
from citrine.resources.predictor_evaluation_workflow import PredictorEvaluationWorkflowCollection
from citrine.resources.design_workflow import DesignWorkflowCollection

from tests.utils.functions import normalize_uid
from tests.utils.fakes import FakeCollection, FakePredictorEvaluationWorkflow

WorkflowType = TypeVar('WorkflowType', bound='Workflow')


class FakeWorkflowCollection(FakeCollection[WorkflowType]):

    def __init__(self, project_id, session: Session):
        FakeCollection.__init__(self)
        self.project_id = project_id
        self.session = session
        self.in_use = {}

    def register(self, workflow: WorkflowType) -> WorkflowType:
        workflow = FakeCollection.register(self, workflow)
        workflow.project_id = self.project_id
        return workflow

    def archive(self, uid: Union[UUID, str] = None, workflow_id: Union[UUID, str] = None):
        if self.in_use.get(normalize_uid(uid), False):
            raise BadRequest("")
        uid = migrate_deprecated_argument(uid, "uid", workflow_id, "workflow_id")
        workflow = self.get(uid)
        workflow.archived = True
        self.update(workflow)


class FakeDesignWorkflowCollection(FakeWorkflowCollection[DesignWorkflow], DesignWorkflowCollection):
    pass


class FakePredictorEvaluationWorkflowCollection(FakeWorkflowCollection[PredictorEvaluationWorkflow], PredictorEvaluationWorkflowCollection):

    def create_default(self, *, predictor_id: UUID) -> PredictorEvaluationWorkflow:
        pew = FakePredictorEvaluationWorkflow(
            name=f"Default predictor evaluation workflow",
            description="",
            evaluators=[]
        )
        pew.project_id = self.project_id
        pew.uid = uuid4()
        pew._session = self.session
        return pew
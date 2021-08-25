from typing import TypeVar, Optional, Union
from uuid import uuid4, UUID

from citrine._session import Session
from citrine.exceptions import NotFound, BadRequest
from citrine.informatics.data_sources import DataSource
from citrine.informatics.design_spaces import DesignSpace, ProductDesignSpace
from citrine.informatics.predictors import Predictor, GraphPredictor
from citrine.informatics.workflows import PredictorEvaluationWorkflow, DesignWorkflow
from citrine.resources.design_space import DesignSpaceCollection
from citrine.resources.module import AbstractModuleCollection
from citrine.resources.predictor import PredictorCollection
from citrine.resources.predictor_evaluation_workflow import PredictorEvaluationWorkflowCollection
from citrine.resources.design_workflow import DesignWorkflowCollection

ModuleType = TypeVar('ModuleType', bound='Module')


def _norm(uid: Union[UUID, str]) -> UUID:
    if isinstance(uid, str):
        return UUID(uid)
    else:
        return uid


class FakeModuleCollection(AbstractModuleCollection[ModuleType]):

    def __init__(self, project_id, session):
        self.project_id = project_id
        self.session: Session = session
        self._modules = {}
        self.in_use = {}

    def register(self, module: ModuleType) -> ModuleType:
        if module.uid is None:
            module.uid = uuid4()
        self._modules[module.uid] = module
        return module

    def update(self, module):
        self._modules.pop(module.uid, None)
        return self.register(module)

    def list(self, page: Optional[int] = None, per_page: int = 100):
        if page is None:
            return iter(list(self._modules.values()))
        else:
            return iter(list(self._modules.values())[(page - 1)*per_page:page*per_page])

    def get(self, uid: Union[UUID, str]) -> ModuleType:
        if _norm(uid) not in self._modules:
            raise NotFound("")
        return self._modules[_norm(uid)]

    def archive(self, uid: Union[UUID, str] = None,
                module_id: Union[UUID, str] = None) -> ModuleType:
        if self.in_use.get(_norm(uid), False):
            raise BadRequest("")
        return AbstractModuleCollection.archive(self, uid, module_id)


class FakeDesignSpaceCollection(FakeModuleCollection[DesignSpace], DesignSpaceCollection):

    def create_default(self, *, predictor_id: UUID) -> DesignSpace:
        return ProductDesignSpace(
            f"Default for {predictor_id}",
            description="",
            dimensions=[],
            subspaces=[]
        )


class FakeDesignWorkflowCollection(FakeModuleCollection[DesignWorkflow], DesignWorkflowCollection):
    pass


class FakePredictorCollection(FakeModuleCollection[Predictor], PredictorCollection):

    def auto_configure(self, *, training_data: DataSource, pattern="PLAIN") -> Predictor:
        return GraphPredictor(
            name=f"Default {pattern.lower()} predictor.",
            description="",
            predictors=[]
        )


class FakePredictorEvaluationWorkflowCollection(
    FakeModuleCollection[PredictorEvaluationWorkflow],
    PredictorEvaluationWorkflowCollection
):
    def create_default(self, *, predictor_id: UUID) -> PredictorEvaluationWorkflow:
        pew = PredictorEvaluationWorkflow(
            name=f"Default for {predictor_id}",
            description="",
            evaluators=[]
        )
        pew.project_id = self.project_id
        pew.uid = uuid4()
        pew._session = self.session
        return pew



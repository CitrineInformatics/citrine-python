from typing import TypeVar, Optional, Union
from uuid import uuid4, UUID

from citrine._session import Session
from citrine.exceptions import NotFound, BadRequest
from citrine.informatics.data_sources import DataSource
from citrine.informatics.design_spaces import DesignSpace, ProductDesignSpace
from citrine.informatics.predictors import Predictor, GraphPredictor
from citrine.resources.design_space import DesignSpaceCollection
from citrine.resources.module import AbstractModuleCollection
from citrine.resources.predictor import PredictorCollection

from tests.utils.fakes import FakeCollection

ModuleType = TypeVar('ModuleType', bound='Module')


def _norm(uid: Union[UUID, str]) -> UUID:
    if isinstance(uid, str):
        return UUID(uid)
    else:
        return uid


class FakeModuleCollection(FakeCollection[ModuleType], AbstractModuleCollection[ModuleType]):

    def __init__(self, project_id, session):
        super().__init__()
        self.project_id = project_id
        self.session: Session = session
        self.in_use = {}

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


class FakePredictorCollection(FakeModuleCollection[Predictor], PredictorCollection):

    def auto_configure(self, *, training_data: DataSource, pattern="PLAIN") -> Predictor:
        return GraphPredictor(
            name=f"Default {pattern.lower()} predictor.",
            description="",
            predictors=[]
        )

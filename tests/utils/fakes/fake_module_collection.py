from typing import TypeVar, Optional, Union
from uuid import uuid4, UUID

from citrine._session import Session
from citrine.exceptions import NotFound, BadRequest
from citrine.informatics.design_spaces import DesignSpace
from citrine.informatics.predictors import Predictor
from citrine.resources.design_space import DesignSpaceCollection
from citrine.resources.module import AbstractModuleCollection
from citrine.resources.predictor import PredictorCollection

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
            return self._modules.values()
        else:
            return list(self._modules.values())[(page - 1)*per_page:page*per_page]

    def get(self, uid: Union[UUID, str]) -> ModuleType:
        if _norm(uid) not in self._modules:
            raise NotFound(f"Cannot find module with uid={uid}")
        return self._modules[_norm(uid)]

    def archive(self, uid: Union[UUID, str] = None,
                module_id: Union[UUID, str] = None) -> ModuleType:
        if self.in_use.get(_norm(uid), False):
            raise BadRequest("Cannot archive a module that is in use")
        return AbstractModuleCollection.archive(self, uid, module_id)


class FakeDesignSpaceCollection(FakeModuleCollection[DesignSpace], DesignSpaceCollection):
    pass


class FakePredictorCollection(FakeModuleCollection[Predictor], PredictorCollection):
    pass



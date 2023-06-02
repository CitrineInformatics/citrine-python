from datetime import datetime
from typing import TypeVar, Union
from uuid import uuid4, UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.exceptions import BadRequest
from citrine.informatics.data_sources import DataSource
from citrine.informatics.design_spaces import DesignSpace, ProductDesignSpace
from citrine.informatics.predictors import GraphPredictor
from citrine.resources.design_space import DesignSpaceCollection
from citrine.resources.predictor import PredictorCollection

from tests.utils.functions import normalize_uid
from tests.utils.fakes import FakeCollection

ModuleType = TypeVar('ModuleType', bound='Module')


class FakeModuleCollection(FakeCollection[ModuleType], Collection[ModuleType]):

    def __init__(self, project_id, session):
        FakeCollection.__init__(self)
        self.project_id = project_id
        self.session: Session = session
        self.in_use = {}

    def archive(self, module_id: UUID):
        if self.in_use.get(normalize_uid(module_id), False):
            raise BadRequest("")

        module = self.get(module_id)
        module.archived_by = uuid4()
        module.archive_time = datetime.now()
        return module

class FakeDesignSpaceCollection(FakeModuleCollection[DesignSpace], DesignSpaceCollection):

    def create_default(self, *, predictor_id: UUID) -> DesignSpace:
        return ProductDesignSpace(
            f"Default design space",
            description="",
            dimensions=[],
            subspaces=[]
        )


class FakePredictorCollection(FakeModuleCollection[GraphPredictor], PredictorCollection):

    def create_default(
            self,
            *,
            training_data: DataSource,
            pattern="PLAIN",
            prefer_valid=True
    ) -> GraphPredictor:
        return GraphPredictor(
            name=f"Default {pattern.lower()} predictor",
            description="",
            predictors=[]
        )
    
    auto_configure = create_default

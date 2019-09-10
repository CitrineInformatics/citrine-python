"""Resources that represent both collections of predictors."""
from uuid import UUID
from typing import TypeVar

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.predictors import Predictor

CreationType = TypeVar('CreationType', bound=Predictor)


class PredictorCollection(Collection[Predictor]):
    """Represents the collection of all projects as well as the resources belonging to it."""

    _path_template = '/projects/{project_id}/modules'
    _individual_key = None
    _collection_key = 'entries'
    _resource = Predictor

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> Predictor:
        """Build an individual Predictor."""
        predictor = Predictor.build(data)
        predictor.session = self.session
        return predictor

    def register(self, model: CreationType) -> CreationType:
        """Registers a Predictor."""
        return super().register(model)

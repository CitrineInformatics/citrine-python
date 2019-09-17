"""Resources that represent both collections of predictors."""
from uuid import UUID
from typing import TypeVar

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.exceptions import CitrineException
from citrine.informatics.predictors import Predictor, SimpleMLPredictor
from citrine.resources.report import ReportResource

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
        self._report_generator = ReportResource(project_id, self.session)

    def build(self, data: dict) -> Predictor:
        """Build an individual Predictor."""
        predictor: Predictor = Predictor.build(data)
        predictor.session = self.session
        if isinstance(predictor, SimpleMLPredictor):
            try:
                predictor.report = self._report_generator.get(data['id'])
            except CitrineException:
                pass
        return predictor

    def register(self, model: CreationType) -> CreationType:
        """Registers a Predictor."""
        return super().register(model)

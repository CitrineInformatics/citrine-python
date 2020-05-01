"""Resources that represent collections of predictors."""
from uuid import UUID
from typing import TypeVar

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.predictors import Predictor

CreationType = TypeVar('CreationType', bound=Predictor)


class PredictorCollection(Collection[Predictor]):
    """[ALPHA] Represents the collection of all predictors for a project.

    Parameters
    ----------
    project_id: UUID
        the UUID of the project

    """

    _path_template = '/projects/{project_id}/modules'
    _individual_key = None
    _resource = Predictor
    _module_type = 'PREDICTOR'

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> Predictor:
        """Build an individual Predictor."""
        predictor: Predictor = Predictor.build(data)
        predictor.session = self.session
        predictor.post_build(self.project_id, data)
        return predictor

from typing import Optional

from citrine.informatics.predictors import Predictor
from citrine.resources.predictor import PredictorCollection


class FakePredictorCollection(PredictorCollection):

    def __init__(self, project_id, session):
        PredictorCollection.__init__(self, project_id=project_id, session=session)
        self.predictors = []

    def register(self, model: Predictor) -> Predictor:
        self.predictors.append(model)
        return model

    def update(self, model):
        self.predictors = [r for r in self.predictors if r.uid != model.uid]
        return self.register(model)

    def list(self, page: Optional[int] = None, per_page: int = 100):
        if page is None:
            return self.predictors
        else:
            return self.predictors[(page - 1)*per_page:page*per_page]
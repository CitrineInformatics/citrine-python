from typing import Set, Optional

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.predictor_evaluation_metrics import PredictorEvaluationMetric


class PredictorEvaluator(PolymorphicSerializable["PredictorEvaluator"]):
    def responses(self) -> Set[str]:
        raise NotImplementedError

    def metrics(self) -> Set[PredictorEvaluationMetric]:
        raise NotImplementedError


class CrossValidationEvaluator(Serializable["CrossValidationEvaluator"], PredictorEvaluator):

    def __init__(self, *,
                 name: str,
                 description: str = "",
                 responses: Set[str],
                 n_folds: int = 5,
                 n_trials: int = 3,
                 metrics: Optional[Set[PredictorEvaluationMetric]] = None,
                 group_together: Optional[Set[str]] = None):
        self.name = name
        self.description = description
        self._responses = responses
        self._metrics = metrics
        self.n_folds = n_folds
        self.n_trials = n_trials
        self.group_together = group_together or {}

    def responses(self) -> Set[str]:
        return self._responses

    def metrics(self) -> Set[PredictorEvaluationMetric]:
        return self._metrics

from typing import Optional, Set, Type

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.predictor_evaluation_metrics import PredictorEvaluationMetric


class PredictorEvaluator(PolymorphicSerializable["PredictorEvaluator"]):
    """[ALPHA] A Citrine Predictor Evaluator computes metrics on a predictor.

    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "CrossValidationEvaluator": CrossValidationEvaluator,
        }[data["type"]]

    def responses(self) -> Set[str]:
        """Responses to compute metrics for."""
        raise NotImplementedError

    def metrics(self) -> Set[PredictorEvaluationMetric]:
        """Metrics to compute for each response."""
        raise NotImplementedError


class CrossValidationEvaluator(Serializable["CrossValidationEvaluator"], PredictorEvaluator):
    """[ALPHA] Performs cross-validation on requested predictor responses and
    computes the requested metrics on each response.

    """
    name = properties.String("name")
    description = properties.String("description")
    _responses = properties.Set(properties.String, "responses")
    n_folds = properties.Integer("n_folds")
    n_trials = properties.Integer("n_trials")
    _metrics = properties.Optional(properties.Set(properties.Object(PredictorEvaluationMetric)), "metrics")
    group_together = properties.Optional(properties.Set(properties.String), "group_together")

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
        """Set of predictor responses cross-validated by the evaluator."""
        return self._responses

    def metrics(self) -> Set[PredictorEvaluationMetric]:
        """Set of metrics computed during cross-validation."""
        return self._metrics

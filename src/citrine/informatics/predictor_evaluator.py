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

    @property
    def responses(self) -> Set[str]:
        """Responses to compute metrics for."""
        raise NotImplementedError

    @property
    def metrics(self) -> Set[PredictorEvaluationMetric]:
        """Metrics to compute for each response."""
        raise NotImplementedError


class CrossValidationEvaluator(Serializable["CrossValidationEvaluator"], PredictorEvaluator):
    """[ALPHA] Performs cross-validation on requested predictor responses and
    computes the requested metrics on each response.

    Parameters
    ----------
    name: str
        Name of the evaluator
    description: str
        Description of the evaluator
    responses: Set[str]
        Set of descriptor keys to evaluate
    n_folds: int
        Number of cross-validation folds
    n_trials: int
        Number of cross-valiation trials, each contains ``n_folds`` folds
    metrics: Optional[Set[PredictorEvaluationMetric]]
        Optional set of metrics to compute for each response.
        Default is all metrics.
    group_together: Optional[Set[str]]
        Set of descriptor keys to group together.
        Candidates with different values for the given keys and identical values
        for all other descriptors will be in the same group.

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
        self.name: str = name
        self.description: str = description
        self._responses: Set[str] = responses
        self._metrics: Optional[Set[PredictorEvaluationMetric]] = metrics
        self.n_folds: int = n_folds
        self.n_trials: int = n_trials
        self.group_together: Optional[Set[str]] = group_together

    @property
    def responses(self) -> Set[str]:
        """Set of predictor responses cross-validated by the evaluator."""
        return self._responses

    @property
    def metrics(self) -> Set[PredictorEvaluationMetric]:
        """Set of metrics computed during cross-validation."""
        return self._metrics

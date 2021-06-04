from typing import Optional, Set, Type, List

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.predictor_evaluation_metrics import PredictorEvaluationMetric

__all__ = ['PredictorEvaluator',
           'CrossValidationEvaluator']


class PredictorEvaluator(PolymorphicSerializable["PredictorEvaluator"]):
    """A Citrine Predictor Evaluator computes metrics on a predictor."""

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "CrossValidationEvaluator": CrossValidationEvaluator,
        }[data["type"]]

    def _attrs(self) -> List[str]:
        raise NotImplementedError  # pragma: no cover

    def __eq__(self, other):
        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in self._attrs()
            ])
        except AttributeError:
            return False

    @property
    def responses(self) -> Set[str]:
        """Responses to compute metrics for."""
        raise NotImplementedError  # pragma: no cover

    @property
    def metrics(self) -> Set[PredictorEvaluationMetric]:
        """Metrics to compute for each response."""
        raise NotImplementedError  # pragma: no cover

    @property
    def name(self) -> str:
        """Name of the evaluator.

        A name is required by all evaluators because it is used as the top-level key
        in the results returned by a
        :class:`citrine.informatics.workflows.PredictorEvaluationWorkflow`.
        As such, the names of all evaluators within a single workflow must be unique.
        """
        raise NotImplementedError  # pragma: no cover


class CrossValidationEvaluator(Serializable["CrossValidationEvaluator"], PredictorEvaluator):
    """Evaluate a predictor via cross validation.

    Performs cross-validation on requested predictor responses and computes the requested metrics
    on each response. For a discussion of how many folds and trials to use,
    please see the :ref:`documentation<Cross-validation evaluator>`.

    In addition to a name, set of responses to validate, trials, folds and metrics to compute,
    this evaluator defines a set of descriptor keys to ignore when grouping.  Candidates with
    different values for ignored keys and identical values for all other predictor inputs will be
    placed in the same fold.  For example, if you are baking cakes with different ingredients and
    different oven temperatures and want to group together the data by the ingredients, then you
    can set `ignore_when_grouping={"oven temperature"}`. That way, two recipes that differ only in
    their oven temperature will always end up in the same fold.

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
        Number of cross-validation trials, each contains ``n_folds`` folds
    metrics: Optional[Set[PredictorEvaluationMetric]]
        Optional set of metrics to compute for each response.
        Default is all metrics.
    ignore_when_grouping: Optional[Set[str]]
        Set of descriptor keys to group together.
        Candidates with different values for the given keys and identical values
        for all other descriptors will be in the same group.

    """

    def _attrs(self) -> List[str]:
        return ["typ", "name", "description",
                "responses", "n_folds", "n_trials", "metrics", "ignore_when_grouping"]

    name = properties.String("name")
    description = properties.String("description")
    _responses = properties.Set(properties.String, "responses")
    n_folds = properties.Integer("n_folds")
    n_trials = properties.Integer("n_trials")
    _metrics = properties.Optional(properties.Set(properties.Object(PredictorEvaluationMetric)),
                                   "metrics")
    ignore_when_grouping = properties.Optional(properties.Set(properties.String),
                                               "ignore_when_grouping")
    typ = properties.String("type", default="CrossValidationEvaluator", deserializable=False)

    def __init__(self,
                 name: str, *,
                 description: str = "",
                 responses: Set[str],
                 n_folds: int = 5,
                 n_trials: int = 3,
                 metrics: Optional[Set[PredictorEvaluationMetric]] = None,
                 ignore_when_grouping: Optional[Set[str]] = None):
        self.name: str = name
        self.description: str = description
        self._responses: Set[str] = responses
        self._metrics: Optional[Set[PredictorEvaluationMetric]] = metrics
        self.n_folds: int = n_folds
        self.n_trials: int = n_trials
        self.ignore_when_grouping: Optional[Set[str]] = ignore_when_grouping

    @property
    def responses(self) -> Set[str]:
        """Set of predictor responses cross-validated by the evaluator."""
        return self._responses

    @property
    def metrics(self) -> Set[PredictorEvaluationMetric]:
        """Set of metrics computed during cross-validation."""
        return self._metrics

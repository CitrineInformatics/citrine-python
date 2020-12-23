from typing import Type, Set

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.predictor_evaluation_metrics import PredictorEvaluationMetric
from citrine.informatics.predictor_evaluator import PredictorEvaluator


__all__ = ['MetricValue',
           'RealMetricValue',
           'PredictedVsActualRealPoint',
           'PredictedVsActualCategoricalPoint',
           'RealPredictedVsActual',
           'CategoricalPredictedVsActual',
           'ResponseMetrics',
           'PredictorEvaluationResult',
           'CrossValidationResult']


class MetricValue(PolymorphicSerializable["MetricValue"]):
    """Value associated with a metric computed during a Predictor Evaluation Workflow."""

    def __init__(self):
        """These are results, so they should be built rather than constructed."""
        pass  # pragma: no cover

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "RealMetricValue": RealMetricValue,
            "RealPredictedVsActual": RealPredictedVsActual,
            "CategoricalPredictedVsActual": CategoricalPredictedVsActual
        }[data["type"]]


class RealMetricValue(Serializable["RealMetricValue"], MetricValue):
    """Mean and standard error computed for a real-valued metric.

    Parameters
    ----------
    mean: float
        Mean value
    standard_error: Optional[float]
        Standard error of the mean

    """

    mean = properties.Float("mean")
    standard_error = properties.Optional(properties.Float(), "standard_error")
    typ = properties.String('type', default='RealMetricValue', deserializable=False)

    def __eq__(self, other):
        if isinstance(other, RealMetricValue):
            return self.mean == other.mean and self.standard_error == other.standard_error
        else:
            return False


class PredictedVsActualRealPoint(Serializable["PredictedVsActualRealPoint"]):
    """Predicted vs. actual data for a single real-valued data point.

    Parameters
    ----------
    uuid: UUID
        Unique Citrine id given to the candidate
    identifiers: Set[str]
        Set of globally unique identfiers given to the candidate
    trial: int
        1-based index of the trial this candidate belonged to
    fold: int
        1-based index of the fold this candidate belonged to
    predicted: RealMetricValue
        Predicted value
    actual: RealMetricValue
        Actual value

    """

    uuid = properties.UUID("uuid")
    identifiers = properties.Set(properties.String, "identifiers")
    trial = properties.Integer("trial")
    fold = properties.Integer("fold")
    predicted = properties.Object(RealMetricValue, "predicted")
    actual = properties.Object(RealMetricValue, "actual")

    def __init__(self):
        pass  # pragma: no cover


class PredictedVsActualCategoricalPoint(Serializable["PredictedVsActualCategoricalPoint"]):
    """Predicted vs. actual data for a single categorical data point.

    Parameters
    ----------
    uuid: UUID
        Unique Citrine id given to the candidate
    identifiers: Set[str]
        Set of globally unique identfiers given to the candidate
    trial: int
        1-based index of the trial this candidate belonged to
    fold: int
        1-based index of the fold this candidate belonged to
    predicted: Mapping[str, float]
        Predicted class probabilities defined as a map from each class name
        to its relative frequency
    actual: Mapping[str, float]
        Actual class probabilities defined as a map from each class name
        to its relative frequency

    """

    uuid = properties.UUID("uuid")
    identifiers = properties.Set(properties.String, "identifiers")
    trial = properties.Integer("trial")
    fold = properties.Integer("fold")
    predicted = properties.Mapping(properties.String, properties.Float, "predicted")
    actual = properties.Mapping(properties.String, properties.Float, "actual")

    def __init__(self):
        pass  # pragma: no cover


class CategoricalPredictedVsActual(Serializable["CategoricalPredictedVsActual"], MetricValue):
    """List of predicted vs. actual data points for a categorical value.

    Parameters
    ----------
    value: List[PredictedVsActualCategoricalPoint]
        List of predicted vs. actual data computed during a predictor evaluation.
        This is a flattened list that contains data for all trials and folds.

    """

    value = properties.List(properties.Object(PredictedVsActualCategoricalPoint), "value")
    typ = properties.String('type', default='CategoricalPredictedVsActual', deserializable=False)

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, item: int):
        return self.value[item]


class RealPredictedVsActual(Serializable["RealPredictedVsActual"], MetricValue):
    """List of predicted vs. actual data points for a real value.

    Parameters
    ----------
    value: List[PredictedVsActualRealPoint]
        List of predicted vs. actual data computed during a predictor evaluation.
        This is a flattened list that contains data for all trials and folds.

    """

    value = properties.List(properties.Object(PredictedVsActualRealPoint), "value")
    typ = properties.String('type', default='RealPredictedVsActual', deserializable=False)

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, item: int):
        return self.value[item]


class ResponseMetrics(Serializable["ResponseMetrics"]):
    """Set of metrics computed by a Predictor Evaluator for a single response.

    Results computed for a metric can be accessed by the metric's ``__repr__`` or
    by the metric itself.

    Parameters
    ----------
    metrics: Mapping[str, MetricValue]
        Metrics computed for a single response, keyed by the metric's ``__repr__``.

    """

    metrics = properties.Mapping(properties.String, properties.Object(MetricValue), "metrics")

    def __init__(self):
        pass  # pragma: no cover

    def __iter__(self):
        return iter(self.metrics)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.metrics[item]
        elif isinstance(item, PredictorEvaluationMetric):
            return self.metrics[repr(item)]
        else:
            raise TypeError("Cannot index ResponseMetrics with a {}".format(type(item)))


class PredictorEvaluationResult(PolymorphicSerializable["PredictorEvaluationResult"]):
    """A Citrine Predictor Evaluation Result.

    This class represents a set of metrics computed by a Predictor Evaluator.
    """

    def __init__(self):
        pass  # pragma: no cover

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "CrossValidationResult": CrossValidationResult,
        }[data["type"]]

    @property
    def evaluator(self) -> PredictorEvaluator:
        """Evaluator that produced the result."""
        raise NotImplementedError  # pragma: no cover

    @property
    def responses(self) -> Set[str]:
        """Predictor responses that were evaluated."""
        raise NotImplementedError  # pragma: no cover

    @property
    def metrics(self) -> Set[PredictorEvaluationMetric]:
        """Metrics computed for predictor responses."""
        raise NotImplementedError  # pragma: no cover


class CrossValidationResult(Serializable["CrossValidationResult"], PredictorEvaluationResult):
    """Result of performing a cross-validation evaluation on a predictor.

    Results for a cross-validated response can be accessed via ``cvResult['response_name']``,
    where ``cvResult`` is a
    :class:`citrine.informatics.predictor_evaluation_result.CrossValidationResult`
    and ``'response_name'`` is a response analyzed by a
    :class:`citrine.informatics.predictor_evaluator.PredictorEvaluator`.

    Parameters
    ----------
    evaluator: PredictorEvaluator
        Evaluator that produced this result.
    response_results: Mapping[str, ResponseMetrics]
        Map from response key to all metrics compute for that response.

    """

    _evaluator = properties.Object(PredictorEvaluator, "evaluator")
    _response_results = properties.Mapping(properties.String, properties.Object(ResponseMetrics),
                                           "response_results")
    typ = properties.String('type', default='CrossValidationResult', deserializable=False)

    def __getitem__(self, item):
        return self._response_results[item]

    def __iter__(self):
        return iter(self.responses)

    @property
    def evaluator(self) -> PredictorEvaluator:
        """Evaluator that produced this result."""
        return self._evaluator

    @property
    def responses(self) -> Set[str]:
        """Responses for which results are present."""
        return set(self._response_results.keys())

    @property
    def metrics(self) -> Set[PredictorEvaluationMetric]:
        """Metrics for which results are present."""
        return self._evaluator.metrics

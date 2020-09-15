from collections import Mapping, Set
from typing import List, Optional, Type
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.predictor_evaluation_metrics import PredictorEvaluationMetric
from citrine.informatics.predictor_evaluator import PredictorEvaluator


class MetricValue(PolymorphicSerializable["MetricValue"]):
    """[ALPHA] Value associated with a metric computed during a Predictor Evaluation Workflow.

    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "RealMetricValue": RealMetricValue,
            "PredictedVsActualValue": PredictedVsActualValue,
        }[data["type"]]


class RealMetricValue(Serializable["RealMetricValue"], MetricValue):
    """[ALPHA] Mean and standard error computed for a real-valued metric

    Parameters
    ----------
    mean: float
        Mean value
    standard_error: float
        Standard error of the mean

    """
    mean = properties.Float("mean")
    standard_error = properties.Optional(properties.Float(), "standard_error")
    typ = properties.String('type', default='RealMetricValue', deserializable=False)

    def __init__(self, *,
                 mean: float,
                 standard_error: Optional[float]):
        self.mean = mean
        self.standard_error = standard_error


class PredictedVsActual(PolymorphicSerializable["PredictedVsActual"]):
    """[ALPHA] Predicted vs. actual data computed for a single data point.

    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "RealPredictedVsActual": RealPredictedVsActual,
            "CategoricalPredictedVsActual": CategoricalPredictedVsActual,
        }[data["type"]]


class RealPredictedVsActual(Serializable["RealPredictedVsActual"], PredictedVsActual):
    """ [ALPHA] Predicted vs. actual data for a single real-valued data point.

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
    typ = properties.String('type', default='RealPredictedVsActual', deserializable=False)

    def __init__(self, *,
                 uuid: UUID,
                 identifiers: Set[str],
                 trial: int,
                 fold: int,
                 predicted: RealMetricValue,
                 actual: RealMetricValue):
        self.uuid = uuid
        self.identifiers = identifiers
        self.trial = trial
        self.fold = fold
        self.predicted = predicted
        self.actual = actual


class CategoricalPredictedVsActual(Serializable["CategoricalPredictedVsActual"], PredictedVsActual):
    """ [ALPHA] Predicted vs. actual data for a single categorical data point.

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
    predicted = properties.Mapping(properties.String, properties.Float, "predicted")
    actual = properties.Mapping(properties.String, properties.Float, "actual")
    typ = properties.String('type', default='CategoricalPredictedVsActual', deserializable=False)

    def __init__(self, *,
                 uuid: UUID,
                 identifiers: Set[str],
                 trial: int,
                 fold: int,
                 predicted: Mapping[str, float],
                 actual: Mapping[str, float]):
        self.uuid = uuid
        self.identifiers = identifiers
        self.trial = trial
        self.fold = fold
        self.predicted = predicted
        self.actual = actual


class PredictedVsActualValue(Serializable["PredictedVsActualValue"], MetricValue):
    """[ALPHA] List of predicted vs. actual data points.

    Parameters
    ----------
    value: List[PredictedVsActual]
        List of predicted vs. actual data computed during a predictor evaluation.
        This is a flattened list that contains data for all trials and folds.

    """
    value = properties.List(properties.Object(PredictedVsActual), "value")
    typ = properties.String('type', default='PredictedVsActualValue', deserializable=False)

    def __init__(self, value: List[PredictedVsActual]):
        self.value = value


class ResponseMetrics(Serializable["ResponseMetrics"]):
    """[ALPHA] Set of metrics computed by a Predictor Evaluator for a single response.
    Results computed for a metric can be accessed by the metric's ``__repr__`` or by the metric itself.

    Parameters
    ----------
    metrics: Mapping[str, MetricValue]
        Metrics computed for a single response, keyed by the metric's ``__repr__``.

    """
    metrics = properties.Mapping(properties.String, properties.Object(MetricValue), "metrics")
    typ = properties.String('type', default='ResponseMetrics', deserializable=False)

    def __init__(self, *, metrics: Mapping[str, MetricValue]):
        self.metrics = metrics

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.metrics[item]
        elif isinstance(item, PredictorEvaluationMetric):
            return self.metrics[repr(item)]
        else:
            raise TypeError("Cannot index ResponseMetrics with a {}".format(type(item)))


class PredictorEvaluationResult(PolymorphicSerializable["PredictorEvaluationResult"]):
    """[ALPHA] A Citrine Predictor Evaluation Result represents a set of metrics
    computed by a Predictor Evaluator.

    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "CrossValidationResult": CrossValidationResult,
        }[data["type"]]

    def evaluator(self) -> PredictorEvaluator:
        """Evaluator that produced the result."""
        raise NotImplementedError()

    def responses(self) -> Set[str]:
        """Predictor responses that were evaluated."""
        raise NotImplementedError()

    def metrics(self) -> Set[PredictorEvaluationMetric]:
        """Metrics computed for predictor responses."""
        raise NotImplementedError()


class CrossValidationResult(Serializable["CrossValidationResult"], PredictorEvaluationResult):
    """[ALPHA] Result of performing a cross-validation evaluation on a predictor.

    Results for a cross-validated response can be accessed via ``cvResult['response_name']``,
    where ``cvResult`` is a
    :class:`citrine.informatics.predictor_evaluation_result.CrossValidationResult`
    and ``'response_key'`` is a response analyzed by a
    :class:`citrine.informatics.predictor_evaluator.PredictorEvaluator`.

    Parameters
    ----------
    evaluator: PredictorEvaluator
        Evaluator that produced this result.
    response_results: Mapping[str, ResponseMetrics]
        Map from response key to all metrics compute for that response.

    """
    _evaluator = properties.Object(PredictorEvaluator, "evaluator")
    _response_results = properties.Mapping(properties.String, properties.Object(ResponseMetrics), "response_results")
    typ = properties.String('type', default='CrossValidationResult', deserializable=False)

    def __init__(self, *,
                 evaluator: PredictorEvaluator,
                 response_results: Mapping[str, ResponseMetrics]):
        self._evaluator = evaluator
        self._response_results = response_results

    def __getitem__(self, item):
        return self._response_results[item]

    def evaluator(self) -> PredictorEvaluator:
        return self._evaluator

    def responses(self) -> Set[str]:
        return set(self._response_results.keys())

    def metrics(self) -> Set[PredictorEvaluationMetric]:
        return self._evaluator.metrics()

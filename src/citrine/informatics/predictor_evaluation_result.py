from collections import Mapping, Set
from typing import Optional
from uuid import UUID

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.predictor_evaluation_metrics import PredictorEvaluationMetric
from citrine.informatics.predictor_evaluator import PredictorEvaluator


class PredictorEvaluationResult(PolymorphicSerializable["PredictorEvaluationResult"]):

    def evaluator(self) -> PredictorEvaluator:
        raise NotImplementedError()

class MetricValue(PolymorphicSerializable["MetricValue"]):
    pass

class RealMetricValue(Serializable["RealMetricValue"], MetricValue):

    def __init__(self, *,
                 mean: float,
                 standard_error: Optional[float]):
        self.mean = mean
        self.standard_error = standard_error

class RealPredictedVsActual(Serializable["RealPredictedVsActual"], MetricValue):

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


class ResponseMetrics(Serializable["ResponseMetrics"]):

    def __init__(self, *, metrics: Mapping[str, MetricValue]):
        self.metrics = metrics

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.metrics[item]
        elif isinstance(item, PredictorEvaluationMetric):
            return self.metrics[repr(item)]
        else:
            raise TypeError("Cannot index ResponseMetrics with a {}".format(type(item)))


class CrossValidationResult(Serializable["CrossValidationResult"], PredictorEvaluationResult):

    def __init__(self, *,
                 evaluator: PredictorEvaluator,
                 response_results: Mapping[str, ResponseMetrics]):
        self._evaluator = evaluator
        self._response_results = response_results

    def evaluator(self) -> PredictorEvaluator:
        return self._evaluator

    def __getitem__(self, item):
        return self._response_results[item]

    def responses(self) -> Set[str]:
        return set(self._response_results.keys())

    def metrics(self) -> Set[PredictorEvaluationMetric]:
        return self._evaluator.metrics()


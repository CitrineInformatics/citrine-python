from typing import Union

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable


class PredictorEvaluationMetric(PolymorphicSerializable["PredictorEvaluationMetric"]):
    pass


class RMSE(Serializable["RMSE"], PredictorEvaluationMetric):

    def __repr__(self):
        return "rmse"

    def __str__(self):
        return "RMSE"


class CoverageProbability(Serializable["CoverageProbability"], PredictorEvaluationMetric):

    def __init__(self, coverage_level: Union[str, float]):
        if isinstance(coverage_level, str):
            if len(coverage_level) != 5 or coverage_level[0:2] != '0.':
                raise ValueError("Coverage level string must have the format '0.###'")
            self._level_str = coverage_level
        elif isinstance(coverage_level, float):
            if coverage_level > 1.0 or coverage_level < 0.0:
                raise ValueError("Coverage level must be between 0 and 1")
            self._level_str = "{:5.3f}".format(coverage_level)

    def __repr__(self):
        return "coverage_probability_{}".format(self._level_str)

    def __str__(self):
        return "Coverage Probability ({})".format(self._level_str)


class CoverageLevel(BaseEnumeration):
    ONE_SIGMA = "one_sigma"
    TWO_SIGMA = "two_sigma"
    THREE_SIGMA = "three_sigma"
    HALF = "50"
    NINETY_FIVE = "95"


class CoverageProb(Serializable["CoverageProb"], PredictorEvaluationMetric):

    def __init__(self, coverage_level: Union[CoverageLevel, str]):
        self.coverage_level = CoverageLevel.get_value(coverage_level)
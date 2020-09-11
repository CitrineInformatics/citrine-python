from typing import Type, Union

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable


class PredictorEvaluationMetric(PolymorphicSerializable["PredictorEvaluationMetric"]):
    """[ALPHA] A Citrine Evaluation Metric represents a metric computed for a predictor.

    Abstract type that returns the proper type given a serialized dict.
    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        t = data["type"]
        return {
            "RMSE": RMSE,
            "NDME": NDME,
            "StandardRMSE": StandardRMSE,
            "PVA": PVA,
            "F1": F1,
            "AreaUnderROC": AreaUnderROC,
            "CoverageProbability": CoverageProbability,
        }[t]


class RMSE(Serializable["RMSE"], PredictorEvaluationMetric):
    typ = properties.String("type", default="RMSE", deserializable=False)

    def __repr__(self):
        return "rmse"

    def __str__(self):
        return "RMSE"


class NDME(Serializable["NDME"], PredictorEvaluationMetric):
    typ = properties.String("type", default="NDME", deserializable=False)

    def __repr__(self):
        return "ndme"

    def __str__(self):
        return "NDME"


class StandardRMSE(Serializable["StandardRMSE"], PredictorEvaluationMetric):
    typ = properties.String("type", default="StandardRMSE", deserializable=False)

    def __repr__(self):
        return "standardized_rmse"

    def __str__(self):
        return "Standardized RMSE"


class PVA(Serializable["PVA"], PredictorEvaluationMetric):
    typ = properties.String("type", default="PVA", deserializable=False)

    def __repr__(self):
        return "predicted_vs_actual"

    def __str__(self):
        return "Predicted vs Actual"


class F1(Serializable["F1"], PredictorEvaluationMetric):
    typ = properties.String("type", default="F1", deserializable=False)

    def __repr__(self):
        return "f1"

    def __str__(self):
        return "F1 Score"


class AreaUnderROC(Serializable["AreaUnderROC"], PredictorEvaluationMetric):
    typ = properties.String("type", default="AreaUnderROC", deserializable=False)

    def __repr__(self):
        return "area_under_roc"

    def __str__(self):
        return "Area Under the ROC"


class CoverageProbability(Serializable["CoverageProbability"], PredictorEvaluationMetric):
    _level_str = properties.String("coverage_level")
    typ = properties.String("type", default="CoverageProbability", deserializable=False)

    def __init__(self, coverage_level: Union[str, float]):
        if isinstance(coverage_level, str):
            if len(coverage_level) != 5 or coverage_level[0:2] != "0.":
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

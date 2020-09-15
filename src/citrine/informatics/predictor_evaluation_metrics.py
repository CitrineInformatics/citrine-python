from typing import Type, Union

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable


class PredictorEvaluationMetric(PolymorphicSerializable["PredictorEvaluationMetric"]):
    """[ALPHA] A metric computed during a Predictor Evaluation Workflow.

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
    """[ALPHA] Root-mean-square error

    """
    typ = properties.String("type", default="RMSE", deserializable=False)

    def __repr__(self):
        return "rmse"

    def __str__(self):
        return "RMSE"


class NDME(Serializable["NDME"], PredictorEvaluationMetric):
    """[ALPHA] Non-dimensional model error

    """
    typ = properties.String("type", default="NDME", deserializable=False)

    def __repr__(self):
        return "ndme"

    def __str__(self):
        return "NDME"


class StandardRMSE(Serializable["StandardRMSE"], PredictorEvaluationMetric):
    """[ALPHA] Standardized root-mean-square error

    """
    typ = properties.String("type", default="StandardRMSE", deserializable=False)

    def __repr__(self):
        return "standardized_rmse"

    def __str__(self):
        return "Standardized RMSE"


class PVA(Serializable["PVA"], PredictorEvaluationMetric):
    """[ALPHA] Predicted vs. actual data.
    Results are returned as a flattened list, where each item represents
    predicted vs. actual data for a single point.

    """
    typ = properties.String("type", default="PVA", deserializable=False)

    def __repr__(self):
        return "predicted_vs_actual"

    def __str__(self):
        return "Predicted vs Actual"


class F1(Serializable["F1"], PredictorEvaluationMetric):
    """[ALPHA] Support-weighted F1 score.

    """
    typ = properties.String("type", default="F1", deserializable=False)

    def __repr__(self):
        return "f1"

    def __str__(self):
        return "F1 Score"


class AreaUnderROC(Serializable["AreaUnderROC"], PredictorEvaluationMetric):
    """[ALPHA] Area under the receiver operating characteristic (ROC) curve.

    """
    typ = properties.String("type", default="AreaUnderROC", deserializable=False)

    def __repr__(self):
        return "area_under_roc"

    def __str__(self):
        return "Area Under the ROC"


class CoverageProbability(Serializable["CoverageProbability"], PredictorEvaluationMetric):
    """[ALPHA] Fraction of observations for which the magnitude of the error is within a
    confidence interval of a given coverage level.

    Parameters
    ----------
    coverage_level: Union[str, float]
        Confidence-interval coverage level.
        The coverage level must both be between 0 and 1.0 (non-inclusive) and specified
        to 3 significant figures.

    """
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

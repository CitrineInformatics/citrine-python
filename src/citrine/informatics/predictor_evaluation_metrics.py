from math import isclose
from typing import Type, Union
from warnings import warn

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
        The coverage level must both be between 0 and 1.0 (non-inclusive) will be rounded
        to 3 significant figures.

    """
    _level_str = properties.String("coverage_level")
    typ = properties.String("type", default="CoverageProbability", deserializable=False)

    def __init__(self, coverage_level: Union[str, float]):
        if isinstance(coverage_level, str):
            try:
                _level_float = float(coverage_level)
            except ValueError:
                raise ValueError(
                    "Invalid coverage level string '{requested_level}'. Coverage level must represent "
                    "a floating point number between 0 and 1 (non-inclusive).".format(
                        requested_level=coverage_level
                    ))
            if _level_float >= 1.0 or _level_float <= 0.0:
                raise ValueError("Coverage level must be between 0 and 1 (non-inclusive).")
            _level_float = round(_level_float, 3)
            if len(coverage_level) > 5:
                warn(
                    "Coverage level can only be specified to 3 decimal places."
                    "Requested level '{requested_level}' will be rounded to {rounded_level}.".format(
                        requested_level=coverage_level,
                        rounded_level=_level_float
                    ))
        elif isinstance(coverage_level, float):
            if coverage_level >= 1.0 or coverage_level <= 0.0:
                raise ValueError("Coverage level must be between 0 and 1 (non-inclusive).")
            _level_float = round(coverage_level, 3)
            if not isclose(coverage_level, _level_float):
                warn(
                    "Coverage level can only be specified to 3 decimal places."
                    "Requested level {requested_level} will be rounded to {rounded_level}.".format(
                        requested_level=coverage_level,
                        rounded_level=_level_float
                    ))

        self._level_str = "{:5.3f}".format(coverage_level)

    def __repr__(self):
        return "coverage_probability_{}".format(self._level_str)

    def __str__(self):
        return "Coverage Probability ({})".format(self._level_str)

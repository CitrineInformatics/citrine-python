from logging import getLogger
from math import isclose
from typing import Type, Union, List

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable

__all__ = ['PredictorEvaluationMetric',
           'RMSE',
           'NDME',
           'RSquared',
           'StandardRMSE',
           'PVA',
           'F1',
           'AreaUnderROC',
           'CoverageProbability']

logger = getLogger(__name__)


class PredictorEvaluationMetric(PolymorphicSerializable["PredictorEvaluationMetric"]):
    """A metric computed during a Predictor Evaluation Workflow.

    Abstract type that returns the proper type given a serialized dict.
    """

    def _attrs(self) -> List[str]:
        return ["typ"]

    def __hash__(self):
        return hash(self.__getattribute__("typ"))

    def __eq__(self, other):
        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in self._attrs()
            ])
        except AttributeError:
            return False

    def __init__(self):
        pass

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        t = data["type"]
        return {
            "RMSE": RMSE,
            "RSquared": RSquared,
            "NDME": NDME,
            "StandardRMSE": StandardRMSE,
            "PVA": PVA,
            "F1": F1,
            "AreaUnderROC": AreaUnderROC,
            "CoverageProbability": CoverageProbability,
        }[t]


class RMSE(Serializable["RMSE"], PredictorEvaluationMetric):
    """Root-mean-square error."""

    typ = properties.String("type", default="RMSE", deserializable=False)

    def __repr__(self):
        return "rmse"

    def __str__(self):
        return "RMSE"


class NDME(Serializable["NDME"], PredictorEvaluationMetric):
    """Non-dimensional model error.

    The non-dimensional model error is the RMSE divided by the standard deviation
    of the labels in the training data (including all folds, not just the training folds).
    """

    typ = properties.String("type", default="NDME", deserializable=False)

    def __repr__(self):
        return "ndme"

    def __str__(self):
        return "NDME"


class RSquared(Serializable["RSquared"], PredictorEvaluationMetric):
    """Fraction of variance explained, commonly known as R^2.

    This dimensionless metric is equal to 1 - (mean squared error / variance of data).
    It is equal to the coefficient of determination calculated with respect to the line
    `predicted = actual`, hence it is commonly referred to as R^2. But unlike R^2 from
    ordinary linear regression, this metric can be negative.
    """

    typ = properties.String("type", default="RSquared", deserializable=False)

    def __repr__(self):
        return "R^2"

    def __str__(self):
        return "R^2"


class StandardRMSE(Serializable["StandardRMSE"], PredictorEvaluationMetric):
    """Standardized root-mean-square error."""

    typ = properties.String("type", default="StandardRMSE", deserializable=False)

    def __repr__(self):
        return "standardized_rmse"

    def __str__(self):
        return "Standardized RMSE"


class PVA(Serializable["PVA"], PredictorEvaluationMetric):
    """Predicted vs. actual data.

    Results are returned as a flattened list, where each item represents
    predicted vs. actual data for a single point.
    """

    typ = properties.String("type", default="PVA", deserializable=False)

    def __repr__(self):
        return "predicted_vs_actual"

    def __str__(self):
        return "Predicted vs Actual"


class F1(Serializable["F1"], PredictorEvaluationMetric):
    """Support-weighted F1 score."""

    typ = properties.String("type", default="F1", deserializable=False)

    def __repr__(self):
        return "f1"

    def __str__(self):
        return "F1 Score"


class AreaUnderROC(Serializable["AreaUnderROC"], PredictorEvaluationMetric):
    """Area under the receiver operating characteristic (ROC) curve."""

    typ = properties.String("type", default="AreaUnderROC", deserializable=False)

    def __repr__(self):
        return "area_under_roc"

    def __str__(self):
        return "Area Under the ROC"


class CoverageProbability(Serializable["CoverageProbability"], PredictorEvaluationMetric):
    """Percentage of observations that fall within a given confidence interval.

    The coverage level can be specified to 3 digits, e.g., 0.123, but not 0.1234.

    Parameters
    ----------
    coverage_level: Union[str, float]
        Confidence-interval coverage level.
        The coverage level must be between 0 and 1.0 (non-inclusive) and will be rounded
        to 3 significant figures.  Default: 0.683 corresponds to one std. deviation

    """

    _level_str = properties.String("coverage_level")
    typ = properties.String("type", default="CoverageProbability", deserializable=False)

    def __init__(self, *, coverage_level: Union[str, float] = "0.683"):
        if isinstance(coverage_level, str):
            try:
                raw_float = float(coverage_level)
            except ValueError:
                raise ValueError(
                    "Invalid coverage level string '{requested_level}'. "
                    "Coverage level must represent a floating point number between "
                    "0 and 1 (non-inclusive).".format(
                        requested_level=coverage_level
                    ))
        elif isinstance(coverage_level, float):
            raw_float = coverage_level
        else:
            raise TypeError("Coverage level must be a string or float")

        if raw_float >= 1.0 or raw_float <= 0.0:
            raise ValueError("Coverage level must be between 0 and 1 (non-inclusive).")
        _level_float = round(raw_float, 3)
        if not isclose(_level_float, raw_float):
            logger.warning(
                "Coverage level can only be specified to 3 decimal places."
                "Requested level '{requested_level}' will be rounded "
                "to {rounded_level}.".format(
                    requested_level=coverage_level,
                    rounded_level=_level_float
                ))

        self._level_str = "{:5.3f}".format(_level_float)

    def _attrs(self) -> List[str]:
        return ["typ", "_level_str"]

    def __repr__(self):
        return "coverage_probability_{}".format(self._level_str)

    def __str__(self):
        return "Coverage Probability ({})".format(self._level_str)

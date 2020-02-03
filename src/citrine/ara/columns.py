"""Column definitions for Ara."""
from typing import Type, Optional, List  # noqa: F401
from abc import abstractmethod

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class Column(PolymorphicSerializable['Column']):
    """[ALPHA] A column in the Ara table, defined as some operation on a variable.

    Abstract type that returns the proper type given a serialized dict.
    """

    @abstractmethod
    def _attrs(self) -> List[str]:
        pass  # pragma: no cover

    def __eq__(self, other):
        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in self._attrs()
            ])
        except AttributeError:
            return False

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        if "type" not in data:
            raise ValueError("Can only get types from dicts with a 'type' key")
        types: List[Type[Serializable]] = [
            IdentityColumn,
            MeanColumn, StdDevColumn, QuantileColumn, OriginalUnitsColumn,
            MostLikelyCategoryColumn, MostLikelyProbabilityColumn
        ]
        res = next((x for x in types if x.typ == data["type"]), None)
        if res is None:
            raise ValueError("Unrecognized type: {}".format(data["type"]))
        return res


class MeanColumn(Serializable['MeanColumn'], Column):
    """[ALPHA] Column containing the mean of a real-valued variable.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column
    target_units: optional[str]
        units to convert the real variable into

    """

    data_source = properties.String('data_source')
    target_units = properties.Optional(properties.String, "target_units")
    typ = properties.String('type', default="mean_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "target_units", "typ"]

    def __init__(self, *,
                 data_source: str,
                 target_units: Optional[str] = None):
        self.data_source = data_source
        self.target_units = target_units


class StdDevColumn(Serializable["StdDevColumn"], Column):
    """[ALPHA] Column containing the standard deviation of a real-valued variable.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column
    target_units: optional[str]
        units to convert the real variable into

    """

    data_source = properties.String('data_source')
    target_units = properties.Optional(properties.String, "target_units")
    typ = properties.String('type', default="std_dev_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "target_units", "typ"]

    def __init__(self, *,
                 data_source: str,
                 target_units: Optional[str] = None):
        self.data_source = data_source
        self.target_units = target_units


class QuantileColumn(Serializable["QuantileColumn"], Column):
    """[ALPHA] Column containing a quantile of the variable.

    The column is populated with the quantile function of the distribution evaluated at "quantile".
    For example, for a uniform distribution parameterized by a lower and upper bound, the value
    in the column would be:
        lower + (upper - lower) * quantile
    while for a normal distribution parameterized by a mean and stddev, the value would be:
        mean + stddev * sqrt(2) * inverse error function (2 * quantile - 1)

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column
    quantile: float
        the quantile to use for the column, defined between 0.0 and 1.0
    target_units: optional[str]
        units to convert the real variable into

    """

    data_source = properties.String('data_source')
    quantile = properties.Float("quantile")
    target_units = properties.Optional(properties.String, "target_units")
    typ = properties.String('type', default="quantile_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "quantile", "target_units", "typ"]

    def __init__(self, *,
                 data_source: str,
                 quantile: float,
                 target_units: Optional[str] = None):
        self.data_source = data_source
        self.quantile = quantile
        self.target_units = target_units


class OriginalUnitsColumn(Serializable["OriginalUnitsColumn"], Column):
    """[ALPHA] Column containing the units as entered in the source data.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column

    """

    data_source = properties.String('data_source')
    typ = properties.String('type', default="original_units_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "typ"]

    def __init__(self, *,
                 data_source: str):
        self.data_source = data_source


class MostLikelyCategoryColumn(Serializable["MostLikelyCategoryColumn"], Column):
    """[ALPHA] Column containing the most likely category.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column

    """

    data_source = properties.String('data_source')
    typ = properties.String('type', default="most_likely_category_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "typ"]

    def __init__(self, *,
                 data_source: str):
        self.data_source = data_source


class MostLikelyProbabilityColumn(Serializable["MostLikelyProbabilityColumn"], Column):
    """[ALPHA] Column containing the probability of the most likely category.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column

    """

    data_source = properties.String('data_source')
    typ = properties.String('type', default="most_likely_probability_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "typ"]

    def __init__(self, *,
                 data_source: str):
        self.data_source = data_source


class IdentityColumn(Serializable['IdentityColumn'], Column):
    """[ALPHA] Column containing the value of a string-valued variable.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column

    """

    data_source = properties.String('data_source')
    typ = properties.String('type', default="identity_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "typ"]

    def __init__(self, *,
                 data_source: str):
        self.data_source = data_source

"""Variable definitions for Ara"""
from typing import Type, Optional, List  # noqa: F401
from abc import abstractmethod

from taurus.entity.link_by_uid import LinkByUID

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class Column(PolymorphicSerializable['Column']):
    """A column in the Ara table, defined as some operation on a variable.

    Abstract type that returns the proper type given a serialized dict.
    """

    @abstractmethod
    def attrs(self) -> List[str]:
        pass  # pragma: no cover

    def __eq__(self, other):
        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in self.attrs()
            ])
        except AttributeError:
            return False

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        types: List[Type[Serializable]] = [
            RealMeanColumn, IdentityColumn
        ]
        return next(x for x in types if x.type == data["type"])


class RealMeanColumn(Serializable['RealMeanColumn'], Column):
    """Column containing the mean of a real-valued variable.

    Parameters
    ----------
    data_source: str
        short_name of the variable to use when populating the column
    target_units: optional[str]
        units to convert the real variable into

    """

    data_source = properties.String('data_source')
    target_units = properties.Optional(properties.String, "target_units")
    type = properties.String('type', default="real_mean_column", deserializable=False)

    def attrs(self) -> List[str]:
        return ["data_source", "target_units", "type"]

    def __init__(self,
                 data_source: str,
                 target_units: Optional[str] = None):
        self.data_source = data_source
        self.target_units = target_units


class IdentityColumn(Serializable['IdentityColumn'], Column):
    """Column containing the value of a string-valued variable.

    Parameters
    ----------
    data_source: str
        short_name of the variable to use when populating the column

    """

    data_source = properties.String('data_source')
    type = properties.String('type', default="identity_column", deserializable=False)

    def attrs(self) -> List[str]:
        return ["data_source", "type"]

    def __init__(self,
                 data_source: str,
                 target_units: Optional[str] = None):
        self.data_source = data_source
        self.target_units = target_units


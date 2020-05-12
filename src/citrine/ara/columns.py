"""Column definitions for Ara."""
from typing import Type, Optional, List  # noqa: F401
from abc import abstractmethod

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class CompositionSortOrder(BaseEnumeration):
    """[ALPHA] Order to use when sorting the components in a composition.

    * ALPHABETICAL is alpha-numeric order by the component name
    * QUANTITY is ordered from the largest to smallest quantity, with ties broken alphabetically
    """

    ALPHABETICAL = "alphabetical"
    QUANTITY = "quantity"


class ChemicalDisplayFormat(BaseEnumeration):
    """[ALPHA] Format to use when rendering a molecular structure.

    * SMILES Simplified molecular-input line-entry system
    * INCHI International Chemical Identifier
    """

    SMILES = "smiles"
    INCHI = "inchi"


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
            MostLikelyCategoryColumn, MostLikelyProbabilityColumn,
            FlatCompositionColumn, ComponentQuantityColumn,
            NthBiggestComponentNameColumn, NthBiggestComponentQuantityColumn,
            MolecularStructureColumn
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


class FlatCompositionColumn(Serializable["FlatCompositionColumn"], Column):
    """[ALPHA] Column that flattens the composition into a string of names and quantities.

    The numeric formatting tries to be human readable. For example, if all of the quantities
    are round numbers like {"spam": 4.0, "eggs": 1.0} then the result omit the decimal points like
    "(spam)4(eggs)1" (if sort_order is by quantity).

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column
    sort_order: CompositionSortOrder
        order with which to sort the components when generating the flat string

    """

    data_source = properties.String('data_source')
    sort_order = properties.Enumeration(CompositionSortOrder, 'sort_order')
    typ = properties.String('type', default="flat_composition_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "sort_order", "typ"]

    def __init__(self, *,
                 data_source: str,
                 sort_order: CompositionSortOrder):
        self.data_source = data_source
        self.sort_order = sort_order


class ComponentQuantityColumn(Serializable["ComponentQuantityColumn"], Column):
    """[ALPHA] Column that extracts the quantity of a given component.

    If the component is not present in the composition, then the value in the column will be 0.0.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column
    component_name: str
        name of the component from which to extract the quantity
    normalize: Optional[bool]
        whether to normalize the quantity by the sum of all component amounts. Default is false

    """

    data_source = properties.String('data_source')
    component_name = properties.String("component_name")
    normalize = properties.Optional(properties.Boolean, "normalize")
    typ = properties.String('type', default="component_quantity_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "component_name", "normalize", "typ"]

    def __init__(self, *,
                 data_source: str,
                 component_name: str,
                 normalize: Optional[bool] = False):
        self.data_source = data_source
        self.component_name = component_name
        self.normalize = normalize


class NthBiggestComponentNameColumn(Serializable["NthBiggestComponentNameColumn"], Column):
    """[ALPHA] Name of the Nth biggest component.

    If there are not N components in the composition, then this column will be empty.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column
    n: int
        index of the component name to extract, starting with 1 for the biggest

    """

    data_source = properties.String('data_source')
    n = properties.Integer("n")
    typ = properties.String('type', default="biggest_component_name_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "n", "typ"]

    def __init__(self, *,
                 data_source: str,
                 n: int):
        self.data_source = data_source
        self.n = n


class NthBiggestComponentQuantityColumn(Serializable["NthBiggestComponentQuantityColumn"], Column):
    """[ALPHA] Quantity of the Nth biggest component.

    If there are not N components in the composition, then this column will be empty.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column
    n: int
        index of the component quantity to extract, starting with 1 for the biggest
    normalize: Optional[bool]
        whether to normalize the quantity by the sum of all component amounts. Default is false

    """

    data_source = properties.String('data_source')
    n = properties.Integer("n")
    normalize = properties.Optional(properties.Boolean, "normalize")
    typ = properties.String('type',
                            default="biggest_component_quantity_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "n", "normalize", "typ"]

    def __init__(self, *,
                 data_source: str,
                 n: int,
                 normalize: Optional[bool] = False):
        self.data_source = data_source
        self.n = n
        self.normalize = normalize


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


class MolecularStructureColumn(Serializable['MolecularStructureColumn'], Column):
    """[ALPHA] Column containing a representation of a molecular structure.

    Parameters
    ----------
    data_source: str
        name of the variable to use when populating the column
    format: ChemicalDisplayFormat
        the format in which to display the molecular structure

    """

    data_source = properties.String('data_source')
    format = properties.Enumeration(ChemicalDisplayFormat, 'format')
    typ = properties.String('type', default="molecular_structure_column", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["data_source", "format", "typ"]

    def __init__(self, *, data_source: str, format: ChemicalDisplayFormat):
        self.data_source = data_source
        self.format = format

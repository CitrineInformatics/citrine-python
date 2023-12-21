"""Tools for working with Descriptors."""
from typing import Type, Set, Union

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties

__all__ = ['Descriptor',
           'RealDescriptor',
           'IntegerDescriptor',
           'ChemicalFormulaDescriptor',
           'MolecularStructureDescriptor',
           'CategoricalDescriptor',
           'FormulationDescriptor',
           'FormulationKey']


class FormulationKey(BaseEnumeration):
    """The allowed names for a FormulationDescriptor.

    * ``HIERARCHICAL`` is the key "Formulation"
    * ``FLAT`` is the key "Flat Formulation"

    """

    HIERARCHICAL = "Formulation"
    FLAT = "Flat Formulation"


class Descriptor(PolymorphicSerializable['Descriptor']):
    """A Descriptor describes the range of values that a quantity can take on.

    Abstract type that returns the proper type given a serialized dict.
    """

    key = properties.String('descriptor_key')

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "Categorical": CategoricalDescriptor,
            "Formulation": FormulationDescriptor,
            "Inorganic": ChemicalFormulaDescriptor,
            "Organic": MolecularStructureDescriptor,
            "Real": RealDescriptor,
            "Integer": IntegerDescriptor,
        }[data["type"]]

    def _equals(self, other, attrs):
        """Check to see if the attrs from the other instance match this instance.

        Returns True if all of the attribute names from attrs match between this and
        the other instance, else False. A missing attribute from this instance will
        raise an AttributeError, and False if missing from the other instance.

        Parameters
        ----------
        other: Description
            the Description instance to compare to
        attrs: List[str]
            A list of attribute names to lookup and compare

        """
        # Check that all attrs exist on this object and raise an AttributeError if not.
        [self.__getattribute__(key) for key in attrs]

        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except AttributeError:
            return False


class RealDescriptor(Serializable['RealDescriptor'], Descriptor):
    """A descriptor to hold real-valued numbers.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor
    lower_bound: float
        inclusive lower bound for valid real values
    upper_bound: float
        inclusive upper bound for valid real values
    units: str
        units string; use an empty string to denote a dimensionless quantity

    """

    lower_bound = properties.Float('lower_bound')
    upper_bound = properties.Float('upper_bound')
    units = properties.String('units', default='')
    typ = properties.String('type', default='Real', deserializable=False)

    def __eq__(self, other):
        return self._equals(other, ["key", "lower_bound", "upper_bound", "units", "typ"])

    def __init__(self,
                 key: str,
                 *,
                 lower_bound: float,
                 upper_bound: float,
                 units: str):
        self.key: str = key
        self.lower_bound: float = lower_bound
        self.upper_bound: float = upper_bound
        self.units = units

    def __str__(self):
        return "<RealDescriptor {!r}>".format(self.key)

    def __repr__(self):
        return "RealDescriptor({}, {}, {}, {})".format(
            self.key, self.lower_bound, self.upper_bound, self.units)


class IntegerDescriptor(Serializable['IntegerDescriptor'], Descriptor):
    """[ALPHA] A descriptor to hold integer-valued numbers.

    Warning: IntegerDescriptors are not fully supported by the Citrine Platform web interface
    and may cause unexpected issues until resolved.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor
    lower_bound: int
        inclusive lower bound for valid integer values
    upper_bound: int
        inclusive upper bound for valid int values

    """

    lower_bound = properties.Integer('lower_bound')
    upper_bound = properties.Integer('upper_bound')
    typ = properties.String('type', default='Integer', deserializable=False)

    def __eq__(self, other):
        return self._equals(other, ["key", "lower_bound", "upper_bound", "typ"])

    def __init__(self, key: str, *, lower_bound: int, upper_bound: int):
        self.key: str = key
        self.lower_bound: int = lower_bound
        self.upper_bound: int = upper_bound

    def __str__(self):
        return "<IntegerDescriptor {!r}>".format(self.key)

    def __repr__(self):
        return "IntegerDescriptor({}, {}, {})".format(self.key, self.lower_bound, self.upper_bound)


class ChemicalFormulaDescriptor(Serializable['ChemicalFormulaDescriptor'], Descriptor):
    """Captures domain-specific context about a stoichiometric chemical formula.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor

    """

    typ = properties.String('type', default='Inorganic', deserializable=False)

    def __eq__(self, other):
        return self._equals(other, ["key", "typ"])

    def __init__(self, key: str):
        self.key: str = key

    def __str__(self):
        return "<ChemicalFormulaDescriptor {!r}>".format(self.key)

    def __repr__(self):
        return "ChemicalFormulaDescriptor(key={})".format(self.key)


class MolecularStructureDescriptor(Serializable['MolecularStructureDescriptor'], Descriptor):
    """
    Material descriptor for an organic molecule.

    Accepts SMILES, IUPAC, and InChI String values.

    Parameters
    ----------
    key: str
        The column header key corresponding to this descriptor

    """

    typ = properties.String('type', default='Organic', deserializable=False)

    def __eq__(self, other):
        return self._equals(other, ["key", "typ"])

    def __init__(self, key: str):
        self.key: str = key

    def __str__(self):
        return "<MolecularStructureDescriptor {!r}>".format(self.key)

    def __repr__(self):
        return "MolecularStructureDescriptor(key={})".format(self.key)


class CategoricalDescriptor(Serializable['CategoricalDescriptor'], Descriptor):
    """A descriptor to hold categorical variables.

    An exhaustive list of categorical values may be supplied.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor
    categories: Set[str]
        possible categories for this descriptor

    """

    typ = properties.String('type', default='Categorical', deserializable=False)
    categories = properties.Set(properties.String, 'descriptor_values')

    def __eq__(self, other):
        return self._equals(other, ["key", "categories", "typ"])

    def __init__(self, key: str, *, categories: Set[str]):
        self.key: str = key
        for category in categories:
            if not isinstance(category, str):
                raise TypeError("All categories must be strings")
        self.categories: Set[str] = categories

    def __str__(self):
        return "<CategoricalDescriptor {!r}>".format(self.key)

    def __repr__(self):
        return "CategoricalDescriptor(key={}, categories={})".format(self.key, self.categories)


class FormulationDescriptor(Serializable['FormulationDescriptor'], Descriptor):
    """A descriptor to hold formulations.

    Parameters
    ----------
    key: str
        The key for the descriptor, which must be either 'Formulation' or 'Flat Formulation'
        to produce valid Citrine Platform assets.
        The two allowed values can be accessed from the `FormulationKey` enum.

    """

    typ = properties.String(
        'type', default=FormulationKey.HIERARCHICAL.value, deserializable=False
    )

    def __init__(self, key: Union[FormulationKey, str]):
        self.key = FormulationKey.from_str(key, exception=True)

    def __eq__(self, other):
        return self._equals(other, ["key", "typ"])

    def __str__(self):
        return f"<FormulationDescriptor '{self.key}'>"

    def __repr__(self):
        return "FormulationDescriptor(key={})".format(self.key)

    @classmethod
    def hierarchical(cls) -> "FormulationDescriptor":
        """The hierarchical formulation descriptor with key 'Formulation'."""
        return FormulationDescriptor(FormulationKey.HIERARCHICAL)

    @classmethod
    def flat(cls) -> "FormulationDescriptor":
        """The flat formulation descriptor with key 'Flat Formulation'."""
        return FormulationDescriptor(FormulationKey.FLAT)

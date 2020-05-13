"""Tools for working with Descriptors."""
from typing import Type, Optional, List  # noqa: F401

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties

__all__ = ['Descriptor',
           'RealDescriptor',
           'ChemicalFormulaDescriptor',
           'InorganicDescriptor',
           'MolecularStructureDescriptor',
           'CategoricalDescriptor',
           'FormulationDescriptor']


class Descriptor(PolymorphicSerializable['Descriptor']):
    """[ALPHA] A Citrine Descriptor describes the range of values that a quantity can take on.

    Abstract type that returns the proper type given a serialized dict.
    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        # Current backend bug PLA-4036 means that some descriptors come back with "category"
        # as type key. This should be resolved soon
        try:
            t = data["type"]
        except KeyError:
            t = data["category"]
        return {
            "Categorical": CategoricalDescriptor,
            "Formulation": FormulationDescriptor,
            "Inorganic": ChemicalFormulaDescriptor,
            "Organic": MolecularStructureDescriptor,
            "Real": RealDescriptor,
        }[t]


class RealDescriptor(Serializable['RealDescriptor'], Descriptor):
    """[ALPHA] A descriptor to hold real-valued numbers.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor
    lower_bound: float
        inclusive lower bound for valid real values
    upper_bound: float
        inclusive upper bound for valid real values

    """

    key = properties.String('descriptor_key')
    lower_bound = properties.Float('lower_bound')
    upper_bound = properties.Float('upper_bound')
    units = properties.Optional(properties.String, 'units', default='')
    typ = properties.String('type', default='Real', deserializable=False)

    def __eq__(self, other):
        try:
            attrs = ["key", "lower_bound", "upper_bound", "units", "typ"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except AttributeError:
            return False

    def __init__(self,
                 key: str,
                 lower_bound: float,
                 upper_bound: float,
                 units: str = ''):
        self.key: str = key
        self.lower_bound: float = lower_bound
        self.upper_bound: float = upper_bound
        self.units: Optional[str] = units

    def __str__(self):
        return "<RealDescriptor {!r}>".format(self.key)


class ChemicalFormulaDescriptor(Serializable['ChemicalFormulaDescriptor'], Descriptor):
    """[ALPHA] Captures domain-specific context about a stoichiometric chemical formula.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor

    """

    key = properties.String('descriptor_key')
    # `threshold` exists in the backend but is not configurable through this client. It is fixed
    # to 1.0 which means that chemical formula string parsing is strict with regards to typos.
    threshold = properties.Float('threshold', deserializable=False, default=1.0)
    typ = properties.String('type', default='Inorganic', deserializable=False)

    def __eq__(self, other):
        try:
            attrs = ["key", "threshold", "typ"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except AttributeError:
            return False

    def __init__(self, key: str):
        self.key: str = key

    def __str__(self):
        return "<ChemicalFormulaDescriptor {!r}>".format(self.key)


def InorganicDescriptor(key: str, threshold: Optional[float] = 1.0):
    """[DEPRECATED] Use ChemicalFormulaDescriptor instead."""
    from warnings import warn
    warn("InorganicDescriptor is deprecated and will soon be removed. "
         "Use ChemicalFormulaDescriptor instead.", DeprecationWarning)
    return ChemicalFormulaDescriptor(key)


class MolecularStructureDescriptor(Serializable['MolecularStructureDescriptor'], Descriptor):
    """
    [ALPHA] Material descriptor for an organic molecule.

    Accepts SMILES, IUPAC, and InChI String values.

    Parameters
    ----------
    key: str
        The column header key corresponding to this descriptor

    """

    key = properties.String('descriptor_key')
    typ = properties.String('type', default='Organic', deserializable=False)

    def __eq__(self, other):
        try:
            attrs = ["key", "typ"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except AttributeError:
            return False

    def __init__(self, key: str):
        self.key: str = key

    def __str__(self):
        return "<MolecularStructureDescriptor {!r}>".format(self.key)


class CategoricalDescriptor(Serializable['CategoricalDescriptor'], Descriptor):
    """[ALPHA] A descriptor to hold categorical variables.

    An exhaustive list of categorical values may be supplied.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor
    categories: list[str]
        possible categories for this descriptor

    """

    key = properties.String('descriptor_key')
    typ = properties.String('type', default='Categorical', deserializable=False)
    categories = properties.List(properties.String, 'descriptor_values')

    def __eq__(self, other):
        try:
            attrs = ["key", "categories", "typ"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ]) and set(self.categories) == set(self.categories + other.categories)
        except AttributeError:
            return False

    def __init__(self, key: str, categories: List[str]):
        self.key: str = key
        self.categories: List[str] = categories

    def __str__(self):
        return "<CategoricalDescriptor {!r}>".format(self.key)


class FormulationDescriptor(Serializable['FormulationDescriptor'], Descriptor):
    """[ALPHA] A descriptor to hold formulations.

    Parameters
    ----------
    key: str
        the key corresponding to a descriptor

    """

    key = properties.String('descriptor_key')
    typ = properties.String('type', default='Formulation', deserializable=False)

    def __eq__(self, other):
        try:
            attrs = ["key", "typ"]
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except AttributeError:
            return False

    def __init__(self, key: str):
        self.key: str = key

    def __str__(self):
        return "<FormulationDescriptor {!r}>".format(self.key)

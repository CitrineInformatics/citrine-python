from typing import Type
from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable


__all__ = [
    'DesignCandidate',
    'DesignMaterial',
    'DesignVariable',
    'MeanAndStd',
    'TopCategories',
    'Mixture',
    'ChemicalFormula',
    'MolecularStructure',
]


class DesignVariable(PolymorphicSerializable["DesignVariable"]):
    """Classes containing data corresponding to individual descriptors.

    If you think of materials as being represented as a set of (descriptor, value) pairs,
    these are simplified representations of the values.
    """

    def __init__(self, arg):
        pass  # pragma: no cover

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "R": MeanAndStd,
            "C": TopCategories,
            "M": Mixture,
            "F": ChemicalFormula,
            "S": MolecularStructure
        }[data["type"]]


class MeanAndStd(Serializable["MeanAndStd"], DesignVariable):
    """The mean and standard deviation of a continuous distribution.

    This does not imply that the distribution is Normal.
    """

    mean = properties.Float('m')
    """:float: mean of the continuous distribution"""
    std = properties.Float('s')
    """:float: standard deviation of the continuous distribution"""

    def __init__(self):
        pass  # pragma: no cover


class TopCategories(Serializable["CategoriesAndProbabilities"], DesignVariable):
    """The category names and probabilities for the most probable categories.

    This list is truncated: these are the most probable categories but other categories
    may have non-zero probabilities.
    """

    probabilities = properties.Mapping(properties.String, properties.Float, 'cp')
    """:Dict[str, float]: mapping from category names to their probabilities"""

    def __init__(self):
        pass  # pragma: no cover


class Mixture(Serializable["Mixture"], DesignVariable):
    """Most likely quantity values for all of the components in a mixture.

    This is a complete list of components with non-zero quantities; there is no
    truncation (but there may be rounding).
    """

    quantities = properties.Mapping(properties.String, properties.Float, 'q')
    """:Dict[str, float]: mapping from ingredient identifiers to their quantities"""

    def __init__(self):
        pass  # pragma: no cover


class ChemicalFormula(Serializable["ChemicalFormula"], DesignVariable):
    """Chemical formula as a string."""

    formula = properties.String('f')
    """:str: chemical formula"""

    def __init__(self):
        pass  # pragma: no cover


class MolecularStructure(Serializable["MolecularStructure"], DesignVariable):
    """SMILES string representation of a molecular structure."""

    smiles = properties.String('s')
    """:str: SMILES string"""

    def __init__(self):
        pass  # pragma: no cover


class DesignMaterial(Serializable["DesignMaterial"]):
    """Description of the material that was designed, as a set of DesignVariables."""

    values = properties.Mapping(properties.String, properties.Object(DesignVariable), 'vars')
    """:Dict[str, DesignVariable]: mapping from descriptor keys to the value for this material"""

    def __init__(self):
        pass  # pragma: no cover


class DesignCandidate(Serializable["DesignCandidate"]):
    """A Citrine Predictor Evaluation Result.

    This class represents the candidate computed by a design execution.
    """

    material_id = properties.UUID('material_id')
    """:UUID: unique Citrine id of the material"""
    identifiers = properties.List(properties.String(), 'identifiers')
    """:List[str]: globally unique identifiers assigned to the material"""
    primary_score = properties.Float('primary_score')
    """:float: numerical score describing how well the candidate satisfies the objectives
    and constraints (higher is better)"""
    material = properties.Object(DesignMaterial, 'material')
    """:DesignMaterial: the material returned by the design workflow"""

    def __init__(self):
        pass  # pragma: no cover

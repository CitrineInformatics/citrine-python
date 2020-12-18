from typing import Type
from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable


__all__ = [
    'DesignCandidate',
    'DesignMaterial',
    'DesignVariable',
    'MeanAndStd',
    'CategoriesAndProbabilities',
    'Mixture',
    'ChemicalFormula',
    'MolecularStructure',
]


class DesignVariable(PolymorphicSerializable["DesignVariable"]):
    """docstring for DesignVariable"""

    def __init__(self, arg):
        pass  # pragma: no cover

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "R": MeanAndStd,
            "C": CategoriesAndProbabilities,
            "M": Mixture,
            "F": ChemicalFormula,
            "S": MolecularStructure
        }[data["type"]]


class MeanAndStd(Serializable["MeanAndStd"], DesignVariable):
    """docstring for MeanAndStd"""

    mean = properties.Float('m')
    std = properties.Float('s')

    def __init__(self):
        pass  # pragma: no cover


class CategoriesAndProbabilities(Serializable["CategoriesAndProbabilities"], DesignVariable):
    """docstring for MeanAndStd"""

    category_probability = properties.Mapping(properties.String, properties.Float, 'cp')

    def __init__(self):
        pass  # pragma: no cover


class Mixture(Serializable["Mixture"], DesignVariable):
    """docstring for MeanAndStd"""

    category_probability = properties.Mapping(properties.String, properties.Float, 'cp')

    def __init__(self):
        pass  # pragma: no cover


class ChemicalFormula(Serializable["ChemicalFormula"], DesignVariable):
    """docstring for MeanAndStd"""

    formula = properties.String('f')

    def __init__(self):
        pass  # pragma: no cover


class MolecularStructure(Serializable["MolecularStructure"], DesignVariable):
    """docstring for MeanAndStd"""

    structure = properties.String('s')

    def __init__(self):
        pass  # pragma: no cover


class DesignMaterial(Serializable["DesignMaterial"]):
    """docstring for Material"""

    vars = properties.Mapping(properties.String, properties.Object(DesignVariable), 'vars')

    def __init__(self):
        pass  # pragma: no cover


class DesignCandidate(Serializable["DesignCandidate"]):
    """A Citrine Predictor Evaluation Result.

    This class represents the candidate computed by a design execution.
    """

    material_id = properties.UUID('material_id')
    identifiers = properties.List(properties.String(), 'identifiers')
    primary_score = properties.Float('primary_score')
    material = properties.Object(DesignMaterial, 'material')

    def __init__(self):
        pass  # pragma: no cover

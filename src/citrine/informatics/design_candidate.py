from typing import Type, Optional

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable


__all__ = [
    'DesignCandidate',
    'HierarchicalDesignCandidate',
    'DesignMaterial',
    'HierarchicalDesignMaterial',
    'SampleSearchSpaceResultCandidate',
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
    typ = properties.String('type', default='R', deserializable=False)
    """:str: polymorphic type code"""

    def __init__(self, *, mean: float, std: float):
        self.mean = mean
        self.std = std
        pass  # pragma: no cover


class TopCategories(Serializable["CategoriesAndProbabilities"], DesignVariable):
    """The category names and probabilities for the most probable categories.

    This list is truncated: these are the most probable categories but other categories
    may have non-zero probabilities.
    """

    probabilities = properties.Mapping(properties.String, properties.Float, 'cp')
    """:Dict[str, float]: mapping from category names to their probabilities"""
    typ = properties.String('type', default='C', deserializable=False)
    """:str: polymorphic type code"""

    def __init__(self, *, probabilities: dict):
        self.probabilities = probabilities
        pass  # pragma: no cover


class Mixture(Serializable["Mixture"], DesignVariable):
    """Most likely quantity values for all of the components in a mixture.

    This is a complete list of components with non-zero quantities; there is no
    truncation (but there may be rounding).
    """

    quantities = properties.Mapping(properties.String, properties.Float, 'q')
    """:Dict[str, float]: mapping from ingredient identifiers to their quantities"""
    labels = properties.Mapping(properties.String, properties.Set(properties.String), 'l')
    """:Dict[str, Set[str]]: mapping from label identifiers to their associated ingredients"""
    typ = properties.String('type', default='M', deserializable=False)
    """:str: polymorphic type code"""

    def __init__(self, *, quantities: dict, labels: Optional[dict] = None):
        self.quantities = quantities
        self.labels = labels or {}
        pass  # pragma: no cover


class ChemicalFormula(Serializable["ChemicalFormula"], DesignVariable):
    """Chemical formula as a string."""

    formula = properties.String('f')
    """:str: chemical formula"""
    typ = properties.String('type', default='F', deserializable=False)
    """:str: polymorphic type code"""

    def __init__(self, *, formula: str):
        self.formula = formula
        pass  # pragma: no cover


class MolecularStructure(Serializable["MolecularStructure"], DesignVariable):
    """SMILES string representation of a molecular structure."""

    smiles = properties.String('s')
    """:str: SMILES string"""
    typ = properties.String('type', default='S', deserializable=False)
    """:str: polymorphic type code"""

    def __init__(self, *, smiles: str):
        self.smiles = smiles
        pass  # pragma: no cover


class DesignMaterial(Serializable["DesignMaterial"]):
    """Description of the material that was designed, as a set of DesignVariables."""

    material_id = properties.UUID('identifiers.id')
    """:UUID: unique internal Citrine id of the material"""
    identifiers = properties.List(properties.String, 'identifiers.external', default=[])
    """:List[str]: globally unique identifiers assigned to the material"""
    process_template = properties.Optional(properties.UUID, 'identifiers.process_template')
    """:Optional[UUID]: GEMD process template that describes the process to create this material"""
    material_template = properties.Optional(properties.UUID, 'identifiers.material_template')
    """:Optional[UUID]: GEMD material template that describes this material"""
    values = properties.Mapping(properties.String, properties.Object(DesignVariable), 'vars')
    """:Dict[str, DesignVariable]: mapping from descriptor keys to the value for this material"""

    def __init__(self, *, values: dict):
        self.values = values
        pass


class HierarchicalDesignMaterial(Serializable["HierarchicalDesignMaterial"]):
    """Description of a designed material as a set of connected individual materials.

    A hierarchical material contains a root material, containing identifiers and variables,
    along any of sub-materials appearing in the history of the root.
    Connections between the root and sub-materials are contained in the mixtures dictionary
    that associates each material (by Citrine ID) with the ingredients that comprise it.
    """

    root = properties.Object(DesignMaterial, 'terminal')
    """:DesignMaterial: root material containing features and predicted properties"""
    sub_materials = properties.List(properties.Object(DesignMaterial), 'sub_materials')
    """:List[DesignMaterial]: all other materials appearing in the history of the root"""
    mixtures = properties.Mapping(properties.UUID, properties.Object(Mixture), 'mixtures')
    """:Dict[UUID, Mixture]: mapping from Citrine ID to components the material is composed of"""


class DesignCandidate(Serializable["DesignCandidate"]):
    """A candidate material generated by the Citrine Platform.

    This class represents the candidate computed by a design execution.
    """

    uid = properties.UUID('id')
    """:UUID: unique external Citrine id of the material"""
    material_id = properties.UUID('material_id')
    """:UUID: unique internal Citrine id of the material"""
    identifiers = properties.List(properties.String(), 'identifiers')
    """:List[str]: globally unique identifiers assigned to the material"""
    primary_score = properties.Float('primary_score')
    """:float: numerical score describing how well the candidate satisfies the objectives
    and constraints (higher is better)"""
    material = properties.Object(DesignMaterial, 'material')
    """:DesignMaterial: the material returned by the design workflow"""


class HierarchicalDesignCandidate(Serializable["HierarchicalDesignCandidate"]):
    """A hierarchical candidate material generated by the Citrine Platform.

    This class represents the candidate computed by a design execution.
    """

    uid = properties.UUID('id')
    """:UUID: unique external Citrine ID of the material"""
    primary_score = properties.Float('primary_score')
    """:float: numerical score describing how well the candidate satisfies the objectives
    and constraints (higher is better)"""
    rank = properties.Integer("rank")
    """:int: rank by score amongst other candidates produced by the design workflow"""
    material = properties.Object(HierarchicalDesignMaterial, "material")
    """:HierarchicalDesignMaterial: the material returned by the design workflow"""


class SampleSearchSpaceResultCandidate(Serializable["SampleSearchSpaceResultCandidate"]):
    """A hierarchical candidate material generated by the Citrine Platform.

    This class represents the candidate computed by a design execution.
    """

    uid = properties.UUID('id')
    """:UUID: unique external Citrine ID of the material"""
    execution_uid = properties.UUID('id')
    """:UUID: unique external Citrine ID of the execution"""
    material = properties.Object(HierarchicalDesignMaterial, "material")
    """:HierarchicalDesignMaterial: the material returned by the design workflow"""

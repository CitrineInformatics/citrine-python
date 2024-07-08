from typing import Dict, List, Optional
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from gemd.enumeration.base_enumeration import BaseEnumeration


class FingerprintType(BaseEnumeration):
    """[ALPHA] Fingerprint type used in Generative Design.

    * AP is the Atom Pairs Fingerprint.
    * PHCO is the Path-Length Connectivity Fingerprint.
    * BPF is the Binary Path Fingerprint.
    * PATH is the Paths of Atoms of Heteroatoms Fingerprint.
    * ECFP4 is the Extended Connectivity Fingerprint with radius 4.
    * ECFP6 is the Extended Connectivity Fingerprint with radius 6.
    * FCFP4 is the Focused Connectivity Fingerprint with radius 4.
    * FCFP6 is the Focused Connectivity Fingerprint with radius 6.
    """

    AP = "AP"
    PHCO = "PHCO"
    BPF = "BPF"
    PATH = "PATH"
    ECFP4 = "ECFP4"
    ECFP6 = "ECFP6"
    FCFP4 = "FCFP4"
    FCFP6 = "FCFP6"


class StructureExclusion(BaseEnumeration):
    """[ALPHA] Structure exclusion type used in Generative Design.

    * `DOUBLE_BONDS` excludes mutation steps that add double bonds.
    * `TRIPLE_BONDS` excludes mutation steps that add triple bonds.
    * `ANIONS` excludes mutation steps that add anions.
    * `CATIONS` excludes mutation steps that add cations.
    * `IONS` excludes mutation steps that add anions and cations.
    * `BORON` excludes mutation steps that add boron atoms.
    * `PHOSPHORUS` excludes mutation steps that add phosphorus atoms.
    * `SULFUR` excludes mutation steps that add sulfur atoms.
    * `NITROGEN` excludes mutation steps that add nitrogen atoms.
    * `OXYGEN` excludes mutation steps that add oxygen atoms.
    * `FLUORINE` excludes mutation steps that add fluorine atoms.
    * `BROMINE` excludes mutation steps that add bromine atoms.
    * `IODINE` excludes mutation steps that add iodine atoms.
    * `CHLORINE` excludes mutation steps that add chlorine atoms.
    """

    DOUBLE_BONDS = "DOUBLE_BONDS"
    TRIPLE_BONDS = "TRIPLE_BONDS"
    ANIONS = "ANIONS"
    CATIONS = "CATIONS"
    IONS = "IONS"
    BORON = "BORON"
    PHOSPHORUS = "PHOSPHORUS"
    SULFUR = "SULFUR"
    NITROGEN = "NITROGEN"
    OXYGEN = "OXYGEN"
    FLUORINE = "FLUORINE"
    BROMINE = "BROMINE"
    IODINE = "IODINE"
    CHLORINE = "CHLORINE"


class GenerativeDesignResult(Serializable["GenerativeDesignResult"]):
    """A Citrine Generation Design Execution Result.

    This class represents the result of a generative design execution.
    """

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        """Run data modification before building."""
        result = data.pop("result")
        data.update(result)
        return data

    uid = properties.UUID('id')
    execution_id = properties.UUID('execution_id')

    seed = properties.String("seed")
    """The seed used to generate the molecule."""
    mutated = properties.String("mutated")
    """The mutated molecule."""
    fingerprint_similarity = properties.Float("fingerprint_similarity")
    """The fingerprint similarity between the seed and the mutated molecule."""
    fingerprint_type = properties.String("fingerprint_type")
    """The fingerprint type used to calculate the fingerprint similarity."""

    def __init__(self):
        pass  # pragma: no cover


class GenerativeDesignInput(Serializable['GenerativeDesignInput']):
    """A Citrine Generative Design Execution Input.

    Parameters
    ----------
    seeds: List[str]
        The seeds used to generate the molecules.
    fingerprint_type: FingerprintType
        The fingerprint type used to calculate the fingerprint similarity.
    min_fingerprint_similarity: float
        The minimum fingerprint similarity between the seed and the mutated molecule.
    mutation_per_seed: int
        The number of initial mutations that will be attempted per seed.
        IMPORTANT, the total number of molecules generated will likely be lower than this value.
        Some mutations may be duplicates or may not meet the fingerprint similarity threshold.
    structure_exclusions: List[StructureExclusion]
        The structure exclusions used to limit molecule mutations.
        If None, no structure exclusions will be used.
    min_substructure_counts: Dict[str, int]
        Dictionary for constraining which substructures (represented by SMARTS strings,
        not SMILES) must appear in each mutated molecule, along with integer values
        representing the minimum number of times each substructure must appear in a
        molecule to be considered a valid mutation.

    """

    seeds = properties.List(properties.String(), 'seeds')
    fingerprint_type = properties.Enumeration(FingerprintType, "fingerprint_type")
    min_fingerprint_similarity = properties.Float("min_fingerprint_similarity")
    mutation_per_seed = properties.Integer("mutation_per_seed")
    structure_exclusions = properties.List(
        properties.Enumeration(StructureExclusion),
        "structure_exclusions"
    )
    min_substructure_counts = properties.Mapping(
        properties.String(), properties.Integer(), "min_substructure_counts",
    )

    def __init__(
        self, *,
        seeds: List[str],
        fingerprint_type: FingerprintType,
        min_fingerprint_similarity: float,
        mutation_per_seed: int,
        structure_exclusions: Optional[List[StructureExclusion]] = None,
        min_substructure_counts: Optional[Dict[str, int]] = None,
    ):
        self.seeds: List[str] = seeds
        self.fingerprint_type: FingerprintType = fingerprint_type
        self.min_fingerprint_similarity: float = min_fingerprint_similarity
        self.mutation_per_seed: int = mutation_per_seed
        self.structure_exclusions: List[StructureExclusion] = structure_exclusions or []
        self.min_substructure_counts: Dict[str, int] = min_substructure_counts or {}

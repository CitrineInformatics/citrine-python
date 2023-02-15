from typing import List
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from gemd.enumeration.base_enumeration import BaseEnumeration


class FingerprintType(BaseEnumeration):
    """[ALPHA] Fingerprint type used in Generative Design.

    * AP is the Atom Pairs Fingerprint.
    * PHCO is the Path-Length Connectivity Fingerprint.
    * BPF is the Binary Path Fingerprint.
    * BTF is the Bit-String Topological Fingerprint.
    * PATH is the Paths of Atoms of Heteroatoms Fingerprint.
    * ECFP4 is the Extended Connectivity Fingerprint with radius 4.
    * ECFP6 is the Extended Connectivity Fingerprint with radius 6.
    * FCFP4 is the Focused Connectivity Fingerprint with radius 4.
    * FCFP6 is the Focused Connectivity Fingerprint with radius 6.
    """

    AP = "AP"
    PHCO = "PHCO"
    BPF = "BPF"
    BTF = "BTF"
    PATH = "PATH"
    ECFP4 = "ECFP4"
    ECFP6 = "ECFP6"
    FCFP4 = "FCFP4"
    FCFP6 = "FCFP6"


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

    """

    seeds = properties.List(properties.String(), 'seeds')
    fingerprint_type = properties.Enumeration(FingerprintType, "fingerprint_type")
    min_fingerprint_similarity = properties.Float("min_fingerprint_similarity")
    mutation_per_seed = properties.Integer("mutation_per_seed")

    def __init__(
        self, *,
        seeds: List[str],
        fingerprint_type: FingerprintType,
        min_fingerprint_similarity: float,
        mutation_per_seed: int
    ):
        self.seeds: List[str] = seeds
        self.fingerprint_type: FingerprintType = fingerprint_type
        self.min_fingerprint_similarity: float = min_fingerprint_similarity
        self.mutation_per_seed: int = mutation_per_seed

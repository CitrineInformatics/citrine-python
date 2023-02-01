from typing import List
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable


class GenerationResult(Serializable["GenerationResult"]):
    """A Citrine Generation Design Result.

    This class represents the molecule greated by a generative design execution.
    """

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


class GenerationExecutionResult(Serializable["GenerationExecutionResult"]):
    """A Citrine Generation Design Execution Result.

    This class represents the result of a generative design execution.
    """

    uid = properties.UUID('id')
    execution_id = properties.UUID('execution_id')
    result = properties.Object(GenerationResult, 'result')

    def __init__(self):
        pass  # pragma: no cover


class GenerativeDesignInput(Serializable['GenerativeDesignInput']):
    """A Citrine Generative Design Execution Input."""

    seeds = properties.List(properties.String(), 'seeds')
    fingerprint_type = properties.String("fingerprint_type")
    min_fingerprint_similarity = properties.Float("min_fingerprint_similarity")
    mutation_per_seed = properties.Integer("mutation_per_seed")

    def __init__(
        self, *,
        seeds: List[str],
        fingerprint_type: str,
        min_fingerprint_similarity: float,
        mutation_per_seed: int
    ):
        self.seeds: List[str] = seeds
        self.fingerprint_type: str = fingerprint_type
        self.min_fingerprint_similarity: float = min_fingerprint_similarity
        self.mutation_per_seed: int = mutation_per_seed

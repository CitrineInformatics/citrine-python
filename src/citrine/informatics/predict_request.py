from typing import List, Optional
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.design_candidate import DesignMaterial


class PredictRequest(Serializable["PredictRequest"]):
    """A request to predict properties for a specific material.

    Typically constructed from an existing design candidate to
    re-predict with modified inputs, or to run a what-if
    analysis on a specific material configuration.

    Parameters
    ----------
    material_id : UUID
        Unique identifier of the material to predict on.
    identifiers : list[str]
        List of identifier strings for this material (e.g.
        sample IDs, lot numbers).
    material : DesignMaterial
        The material definition containing descriptor values
        to use as predictor inputs.
    created_from_id : UUID
        The UID of the design candidate this request was
        derived from.
    random_seed : int, optional
        Seed for reproducible stochastic predictions. If
        omitted, the platform chooses a random seed.

    """

    material_id = properties.UUID('material_id')
    identifiers = properties.List(properties.String(), 'identifiers')
    material = properties.Object(DesignMaterial, 'material')
    created_from_id = properties.UUID('created_from_id')
    random_seed = properties.Optional(properties.Integer, 'random_seed')

    def __init__(self, material_id: UUID,
                 identifiers: List[str],
                 material: DesignMaterial,
                 created_from_id: UUID,
                 *,
                 random_seed: Optional[int] = None):
        self.material_id = material_id
        self.identifiers = identifiers
        self.material = material
        self.created_from_id = created_from_id
        self.random_seed = random_seed

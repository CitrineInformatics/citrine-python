from typing import List, Optional
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.design_candidate import DesignMaterial

__all__ = ['SinglePredictRequest']


class SinglePredictRequest(Serializable["SinglePredictRequest"]):
    """A Citrine Single Predict Request.

    This class represents a request to make a prediction against a predictor.
    """

    material_id = properties.UUID('material_id')
    identifiers = properties.List(properties.String(), 'identifiers')
    material = properties.Object(DesignMaterial, 'material')
    random_seed = properties.Optional(properties.Integer, 'random_seed')

    def __init__(self, material_id: UUID,
                 identifiers: List[str],
                 material: DesignMaterial,
                 *,
                 random_seed: Optional[int] = None):
        self.material_id = material_id
        self.identifiers = identifiers
        self.material = material
        self.random_seed = random_seed

from typing import List, Optional
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.design_candidate import DesignMaterial


class PredictRequest(Serializable["PredictRequest"]):
    """A Citrine Predict Request.

    This class represents the candidate computed by a design execution.
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

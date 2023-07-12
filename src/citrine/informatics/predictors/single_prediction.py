from typing import List
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.design_candidate import DesignMaterial

__all__ = ['SinglePrediction']


class SinglePrediction(Serializable["SinglePrediction"]):
    """A Citrine Single Prediction.

    This class represents the result of a prediction made using a predictor.
    """

    material_id = properties.UUID('material_id')
    identifiers = properties.List(properties.String(), 'identifiers')
    material = properties.Object(DesignMaterial, 'material')

    def __init__(self, material_id: UUID,
                 identifiers: List[str],
                 material: DesignMaterial):
        self.material_id = material_id
        self.identifiers = identifiers
        self.material = material

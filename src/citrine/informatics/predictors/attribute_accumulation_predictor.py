from typing import List

from citrine._rest.resource import Resource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import PredictorNode


class AttributeAccumulationPredictor(Resource["AttributeAccumulationPredictor"], PredictorNode):
    """A node to support propagating attributes through training.

    You should never have to add this node yourself: the backend should be able to automatically
    create it when necessary.
    """

    attributes = _properties.List(_properties.Object(Descriptor), 'attributes')
    sequential = _properties.Boolean('sequential')

    typ = _properties.String('type', default='AttributeAccumulation', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 attributes: List[Descriptor],
                 sequential: bool):
        self.name = name
        self.description = description
        self.attributes = attributes
        self.sequential = sequential

    def __str__(self):
        return '<AttributeAccumulationPredictor {!r}>'.format(self.name)

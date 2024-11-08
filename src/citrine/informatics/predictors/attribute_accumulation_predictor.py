from typing import List

from citrine._rest.resource import Resource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import PredictorNode

__all__ = ['AttributeAccumulationPredictor']


class AttributeAccumulationPredictor(Resource["AttributeAccumulationPredictor"], PredictorNode):
    """A predictor that computes an output from an expression and set of bounded inputs.

    For a discussion of expression syntax and a list of allowed symbols,
    please see the :ref:`documentation<Attribute Accumulation>`.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    attributes: List[Descriptor]
        the attributes that are accumulated from ancestor nodes

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
        self.name: str = name
        self.description: str = description
        self.attributes: List[Descriptor] = attributes
        self.sequential: bool = sequential

    def __str__(self):
        return '<AttributeAccumulationPredictor {!r}>'.format(self.name)

from typing import Set

from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.predictors import Predictor

__all__ = ['LabelFractionsPredictor']


class LabelFractionsPredictor(
        EngineResource['LabelFractionsPredictor'], Predictor):
    """A predictor interface that computes the relative proportions of labeled ingredients.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    input_descriptor: FormulationDescriptor
        descriptor that contains formulation data
    labels: Set[str]
        labels to compute the quantity fractions of

    """

    input_descriptor = _properties.Object(FormulationDescriptor, 'data.instance.input')
    labels = _properties.Set(_properties.String, 'data.instance.labels')

    typ = _properties.String('data.instance.type', default='LabelFractions',
                             deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 labels: Set[str]):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.labels: Set[str] = labels

    def __str__(self):
        return '<LabelFractionsPredictor {!r}>'.format(self.name)

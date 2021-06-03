from typing import Set

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.predictors import Predictor
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['LabelFractionsPredictor']


class LabelFractionsPredictor(Resource['LabelFractionsPredictor'], Predictor, AIResourceMetadata):
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

    _resource_type = ResourceTypeEnum.MODULE

    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    labels = _properties.Set(_properties.String, 'config.labels')

    typ = _properties.String('config.type', default='LabelFractions',
                             deserializable=False)
    module_type = _properties.String('module_type', default='PREDICTOR')

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

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<LabelFractionsPredictor {!r}>'.format(self.name)

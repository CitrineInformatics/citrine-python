from typing import Set, Mapping

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
from citrine.informatics.predictors import Predictor
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['IngredientsToFormulationPredictor']


class IngredientsToFormulationPredictor(
        Resource['IngredientsToFormulationPredictor'], Predictor, AIResourceMetadata):
    """[ALPHA] A predictor interface that constructs a formulation from ingredient quantities.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    output: FormulationDescriptor
        descriptor that represents the output formulation
    id_to_quantity: Mapping[str, RealDescriptor]
        Map from ingredient identifier to the descriptor that represents its quantity,
        e.g., ``{'water': RealDescriptor('water quantity', 0, 1, "")}``
    labels: Mapping[str, Set[str]]
        Map from each label to all ingredients assigned that label, when present in a mixture,
        e.g., ``{'solvent': {'water'}}``

    """

    _resource_type = ResourceTypeEnum.MODULE

    output = _properties.Object(FormulationDescriptor, 'config.output')
    id_to_quantity = _properties.Mapping(_properties.String, _properties.Object(RealDescriptor),
                                         'config.id_to_quantity')
    labels = _properties.Mapping(_properties.String, _properties.Set(_properties.String),
                                 'config.labels')

    typ = _properties.String('config.type', default='IngredientsToSimpleMixture',
                             deserializable=False)
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 output: FormulationDescriptor,
                 id_to_quantity: Mapping[str, RealDescriptor],
                 labels: Mapping[str, Set[str]]):
        self.name: str = name
        self.description: str = description
        self.output: FormulationDescriptor = output
        self.id_to_quantity: Mapping[str, RealDescriptor] = id_to_quantity
        self.labels: Mapping[str, Set[str]] = labels

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<IngredientsToFormulationPredictor {!r}>'.format(self.name)

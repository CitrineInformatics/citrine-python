from typing import Set, Mapping
from warnings import warn

from citrine._rest.resource import Resource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
from citrine.informatics.predictors import Predictor

__all__ = ['IngredientsToSimpleMixturePredictor']


class IngredientsToSimpleMixturePredictor(
        Resource['IngredientsToSimpleMixturePredictor'], Predictor):
    """[ALPHA] A predictor interface that constructs a simple mixture from ingredient quantities.

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

    output = _properties.Object(FormulationDescriptor, 'config.output')
    id_to_quantity = _properties.Mapping(_properties.String, _properties.Object(RealDescriptor),
                                         'config.id_to_quantity')
    labels = _properties.Mapping(_properties.String, _properties.Set(_properties.String),
                                 'config.labels')
    typ = _properties.String('config.type', default='IngredientsToSimpleMixture',
                             deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 output: FormulationDescriptor,
                 id_to_quantity: Mapping[str, RealDescriptor],
                 labels: Mapping[str, Set[str]],
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.output: FormulationDescriptor = output
        self.id_to_quantity: Mapping[str, RealDescriptor] = id_to_quantity
        _labels = {}
        for label, ingredients in labels.items():
            if not isinstance(ingredients, set):
                warn(f"Labels for predictor '{self.name}' must be specified as a mapping from "
                     "each label to a set of ingredient names. Support for other collections "
                     "is deprecated and will be removed in a future release.",
                     DeprecationWarning)
                _labels[label] = set(ingredients)
            else:
                _labels[label] = ingredients
        self.labels: Mapping[str, Set[str]] = _labels
        self.archived: bool = archived

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<IngredientsToSimpleMixturePredictor {!r}>'.format(self.name)

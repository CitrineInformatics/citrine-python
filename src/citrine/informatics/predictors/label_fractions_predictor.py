from typing import Set
from warnings import warn

from citrine._rest.resource import Resource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.predictors import Predictor

__all__ = ['LabelFractionsPredictor']


class LabelFractionsPredictor(Resource['LabelFractionsPredictor'], Predictor):
    """[ALPHA] A predictor interface that computes the relative proportions of labeled ingredients.

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

    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    labels = _properties.Set(_properties.String, 'config.labels')
    typ = _properties.String('config.type', default='LabelFractions',
                             deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 labels: Set[str],
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        if not isinstance(labels, set):
            warn(f"Labels for predictor '{self.name}' must be specified as a set of strings."
                 "Support for other collections is deprecated and will be removed in a "
                 "future release.",
                 DeprecationWarning)
            _labels = set(labels)
        else:
            _labels = labels
        self.labels: Set[str] = _labels
        self.archived: bool = archived

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<LabelFractionsPredictor {!r}>'.format(self.name)

from typing import List, Optional

from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.reports import Report
from citrine.informatics.predictors import Predictor

__all__ = ['LabelFractionsPredictor']


class LabelFractionsPredictor(Serializable['LabelFractionsPredictor'], Predictor):
    """[ALPHA] A predictor interface that computes the relative proportions of labeled ingredients.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    input_descriptor: FormulationDescriptor
        descriptor that contains formulation data
    labels: List[str]
        labels to compute the quantity fractions of

    """

    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    labels = _properties.List(_properties.String, 'config.labels')
    typ = _properties.String('config.type', default='LabelFractions',
                             deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 labels: List[str],
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.labels: List[str] = labels
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.archived: bool = archived

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<LabelFractionsPredictor {!r}>'.format(self.name)

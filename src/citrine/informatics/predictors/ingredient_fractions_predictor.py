from typing import List, Optional

from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.reports import Report
from citrine.informatics.predictors import Predictor

__all__ = ['IngredientFractionsPredictor']


class IngredientFractionsPredictor(Serializable["IngredientFractionsPredictor"], Predictor):
    """[ALPHA] A predictor interface that computes ingredient fractions.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    input_descriptor: FormulationDescriptor
        descriptor that represents the input formulation
    ingredients: List[str]
        list of ingredients to featurize.
        This list should contain all possible ingredients.
        If an unknown ingredient is encountered, an error will be thrown.

    """

    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    ingredients = _properties.List(_properties.String, 'config.ingredients')

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    typ = _properties.String('config.type', default='IngredientFractions',
                             deserializable=False)

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 ingredients: List[str],
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.ingredients: List[str] = ingredients
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.archived: bool = archived

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<IngredientFractionsPredictor {!r}>'.format(self.name)

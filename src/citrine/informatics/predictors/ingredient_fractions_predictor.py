from typing import Set

from citrine._rest.resource import Resource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.predictors import PredictorNode

__all__ = ['IngredientFractionsPredictor']


class IngredientFractionsPredictor(Resource["IngredientFractionsPredictor"], PredictorNode):
    """A predictor interface that computes ingredient fractions.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    input_descriptor: FormulationDescriptor
        descriptor that represents the input formulation
    ingredients: Set[str]
        set of ingredients to featurize.
        If an unknown ingredient is encountered, an error will be thrown.

    """

    input_descriptor = _properties.Object(FormulationDescriptor, 'input')
    ingredients = _properties.Set(_properties.String, 'ingredients')

    typ = _properties.String('type', default='IngredientFractions', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 ingredients: Set[str]):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.ingredients: Set[str] = ingredients

    def __str__(self):
        return '<IngredientFractionsPredictor {!r}>'.format(self.name)

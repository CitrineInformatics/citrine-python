from typing import Type

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine.informatics.predictors import Predictor


class PredictorNode(PolymorphicSerializable["PredictorNode"], Predictor):
    """An individual compute node within a Predictor.

    A PredictorNode cannot be registered to the Citrine Platform by itself
    and must be included as a component within a GraphPredictor to be used.

    """

    name = properties.String("name")
    description = properties.Optional(properties.String(), "description")

    @classmethod
    def get_type(cls, data) -> Type['PredictorNode']:
        """Return the subtype."""
        from .expression_predictor import ExpressionPredictor
        from .molecular_structure_featurizer import MolecularStructureFeaturizer
        from .ingredients_to_formulation_predictor import IngredientsToFormulationPredictor
        from .label_fractions_predictor import LabelFractionsPredictor
        from .simple_mixture_predictor import SimpleMixturePredictor
        from .ingredient_fractions_predictor import IngredientFractionsPredictor
        from .auto_ml_predictor import AutoMLPredictor
        from .mean_property_predictor import MeanPropertyPredictor
        from .chemical_formula_featurizer import ChemicalFormulaFeaturizer
        type_dict = {
            "AnalyticExpression": ExpressionPredictor,
            "MoleculeFeaturizer": MolecularStructureFeaturizer,
            "IngredientsToSimpleMixture": IngredientsToFormulationPredictor,
            "MeanProperty": MeanPropertyPredictor,
            "LabelFractions": LabelFractionsPredictor,
            "SimpleMixture": SimpleMixturePredictor,
            "IngredientFractions": IngredientFractionsPredictor,
            "ChemicalFormulaFeaturizer": ChemicalFormulaFeaturizer,
            "AutoML": AutoMLPredictor,
        }
        typ = type_dict.get(data['type'])
        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid predictor node type. '
                'Must be in {}.'.format(data['type'], type_dict.keys())
            )

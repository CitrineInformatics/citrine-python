from typing import Type

from citrine._serialization import properties
from citrine.informatics.modules import Module
from citrine.resources.report import ReportResource


__all__ = ['Predictor']


class Predictor(Module):
    """Module that describes the ability to compute/predict properties of materials.

    Abstract type that returns the proper type given a serialized dict. Subtype
    based on the 'type' value of the passed in dict.

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    """:Optional[UUID]: Citrine Platform unique identifier"""
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')

    @property
    def report(self):
        """Fetch the predictor report."""
        if self.uid is None or self._session is None or self._project_id is None:
            msg = "Cannot get the report for a predictor that wasn't read from the platform"
            raise ValueError(msg)
        return ReportResource(self._project_id, self._session).get(self.uid)

    @classmethod
    def get_type(cls, data) -> Type['Predictor']:
        """Return the subtype."""
        from .simple_ml_predictor import SimpleMLPredictor
        from .graph_predictor import GraphPredictor
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
            "Simple": SimpleMLPredictor,
            "Graph": GraphPredictor,
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
        typ = type_dict.get(data['config']['type'])

        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid predictor type. '
                'Must be in {}.'.format(data['config']['type'], type_dict.keys())
            )

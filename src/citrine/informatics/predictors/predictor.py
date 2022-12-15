from typing import Optional, Type
from uuid import UUID

from deprecation import deprecated

from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._session import Session
from citrine.resources.report import ReportResource


__all__ = ['Predictor']


class Predictor(PolymorphicSerializable['Predictor'], AsynchronousObject):
    """Module that describes the ability to compute/predict properties of materials.

    Abstract type that returns the proper type given a serialized dict. Subtype
    based on the 'type' value of the passed in dict.

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    """:Optional[UUID]: Citrine Platform unique identifier"""
    name = properties.String('data.name')
    description = properties.Optional(properties.String(), 'data.description')

    _response_key = None
    _project_id: Optional[UUID] = None
    _session: Optional[Session] = None
    _in_progress_statuses = ["VALIDATING", "CREATED"]
    _succeeded_statuses = ["READY"]
    _failed_statuses = ["INVALID", "ERROR"]

    @property
    @deprecated(deprecated_in="1.31.0", removed_in="2.0.0",
                details="Please use `isinstance` or `issubclass` instead.")
    def module_type(self):
        """The type of module."""
        return "PREDICTOR"

    @module_type.setter
    @deprecated(deprecated_in="1.31.0", removed_in="2.0.0")
    def module_type(self, value):
        pass

    @property
    def report(self):
        """Fetch the predictor report."""
        if self.uid is None or self._session is None or self._project_id is None \
                or getattr(self, "version", None) is None:
            msg = "Cannot get the report for a predictor that wasn't read from the platform"
            raise ValueError(msg)
        report_resource = ReportResource(self._project_id, self._session)
        return report_resource.get(predictor_id=self.uid, predictor_version=self.version)

    @staticmethod
    def wrap_instance(predictor_data: dict) -> dict:
        """Insert a serialized embedded predictor into a module envelope.

        This facilitates deserialization.
        """
        return {
            "data": {
                "name": predictor_data.get("name", ""),
                "description": predictor_data.get("description", ""),
                "instance": predictor_data
            }
        }

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
        typ = type_dict.get(data['data']['instance']['type'])

        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid predictor type. '
                'Must be in {}.'.format(data['data']['instance']['type'], type_dict.keys())
            )

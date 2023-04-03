import warnings
from typing import Optional, Type, List
from uuid import UUID

from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._session import Session
from citrine.informatics.data_sources import DataSource
from citrine.resources.report import ReportResource
from citrine.informatics.predictors.single_predict_request import SinglePredictRequest
from citrine.informatics.predictors.single_prediction import SinglePrediction
from citrine._utils.functions import format_escaped_url

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
    version = properties.Optional(
        properties.Union([properties.Integer(), properties.String()]),
        'metadata.version', serializable=False)

    _response_key = None
    _project_id: Optional[UUID] = None
    _session: Optional[Session] = None
    _in_progress_statuses = ["VALIDATING", "CREATED"]
    _succeeded_statuses = ["READY"]
    _failed_statuses = ["INVALID", "ERROR"]
    _api_version = "v3"

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

    def _path(self):
        return format_escaped_url(
            '/projects/{project_id}/predictors/{predictor_id}/versions/{version}',
            project_id=self._project_id,
            predictor_id=str(self.uid),
            version=self.version
        )

    def predict(self,
                predict_request: SinglePredictRequest) -> SinglePrediction:
        """Make a one-off prediction with this predictor."""
        path = self._path() + '/predict'
        res = self._session.post_resource(path, predict_request.dump(), version=self._api_version)
        return SinglePrediction.build(res)

    @classmethod
    def _check_deprecated_training_data(cls, training_data: Optional[List[DataSource]]) -> None:
        if training_data is not None:
            warnings.warn(
                f"The field `training_data` on {cls.__name__} predictors is deprecated "
                "and will be removed in version 3.0.0. Include training data for all "
                "sub-predictors on the parent GraphPredictor. Existing training data "
                "on this predictor will be moved to the parent GraphPredictor upon registration.",
                DeprecationWarning
            )

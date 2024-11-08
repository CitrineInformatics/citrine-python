from typing import List, Optional
from uuid import UUID

from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._rest.engine_resource import VersionedEngineResource
from citrine._serialization import properties as properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.informatics.data_sources import DataSource
from citrine.informatics.predictors.single_predict_request import SinglePredictRequest
from citrine.informatics.predictors.single_prediction import SinglePrediction
from citrine.informatics.predictors import PredictorNode, Predictor
from citrine.resources.report import ReportResource

__all__ = ['GraphPredictor']


class GraphPredictor(VersionedEngineResource['GraphPredictor'], AsynchronousObject, Predictor):
    """A predictor interface that stitches individual predictor nodes together.

    The GraphPredictor is the only predictor that can be registered on the Citrine Platform
    and carries along its meta-data regarding versioning, platform identifiers, and updates.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    predictors: List[Union[UUID, PredictorNode]],
        the list of individual predictors to use in the graph
    training_data: Optional[List[DataSource]]
        Optional sources of training data shared by all predictors in the graph.
        Training data provided by this graph predictor does not need to be specified as part of the
        configuration of sub-predictors. Shared training data and any training data specified
        by a sub-predictor will be combined into a flattened list and de-duplicated
        by uid and identifiers. De-duplication is performed if a uid or identifier is shared
        between two or more rows. The content of a de-duplicated row will contain the union of
        data across all rows that share the same uid or at least 1 identifier.

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    """:Optional[UUID]: Citrine Platform unique identifier"""

    name = properties.String('data.name')
    description = properties.Optional(properties.String(), 'data.description')
    predictors = properties.List(properties.Object(PredictorNode), 'data.instance.predictors')

    # the default seems to be defined in instances, not the class itself
    # this is tested in test_graph_default_training_data
    training_data = properties.List(
        properties.Object(DataSource), 'data.instance.training_data', default=[]
    )

    version = properties.Optional(
        properties.Union([properties.Integer(), properties.String()]),
        'metadata.version',
        serializable=False
    )

    _api_version = "v3"
    _response_key = None
    _project_id: Optional[UUID] = None
    _session: Optional[Session] = None
    _in_progress_statuses = ["VALIDATING", "CREATED"]
    _succeeded_statuses = ["READY"]
    _failed_statuses = ["INVALID", "ERROR"]

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 predictors: List[PredictorNode],
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        self.training_data: List[DataSource] = training_data or []
        self.predictors: List[PredictorNode] = predictors

    def __str__(self):
        return '<GraphPredictor {!r}>'.format(self.name)

    def _path(self):
        return format_escaped_url(
            '/projects/{project_id}/predictors/{predictor_id}/versions/{version}',
            project_id=self._project_id,
            predictor_id=str(self.uid),
            version=self.version
        )

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

    @property
    def report(self):
        """Fetch the predictor report."""
        if self.uid is None or self._session is None or self._project_id is None \
                or getattr(self, "version", None) is None:
            msg = "Cannot get the report for a predictor that wasn't read from the platform"
            raise ValueError(msg)
        report_resource = ReportResource(self._project_id, self._session)
        return report_resource.get(predictor_id=self.uid, predictor_version=self.version)

    def predict(self, predict_request: SinglePredictRequest) -> SinglePrediction:
        """Make a one-off prediction with this predictor."""
        path = self._path() + '/predict'
        res = self._session.post_resource(path, predict_request.dump(), version=self._api_version)
        return SinglePrediction.build(res)

    def _convert_to_multistep(self) -> "GraphPredictor":
        """Make the GraphPredictor look as if generated with a MULTISTEP_MATERIALS datasource."""
        from citrine.informatics.predictors import (
            AttributeAccumulationPredictor, MolecularStructureFeaturizer,
            LabelFractionsPredictor, SimpleMixturePredictor, IngredientFractionsPredictor,
            AutoMLPredictor, MeanPropertyPredictor, ChemicalFormulaFeaturizer
        )

        automl_outputs = {}
        featurizer_outputs = set()
        automl_inputs = {}

        for predictor in self.predictors:
            if isinstance(predictor, AttributeAccumulationPredictor):
                raise ValueError("Graph already contains Attribute Accumulation nodes")
            elif isinstance(predictor, AutoMLPredictor):
                for descriptor in predictor.outputs:
                    automl_outputs[descriptor.key] = descriptor
                for descriptor in predictor.inputs:
                    automl_inputs[descriptor.key] = descriptor
            elif isinstance(predictor, MeanPropertyPredictor):
                for descriptor in predictor.properties:
                    featurizer_outputs.add(
                        f"mean of property {descriptor.key} in {predictor.input_descriptor.key}"
                    )
            elif isinstance(predictor, IngredientFractionsPredictor):
                for ingredient in predictor.ingredients:
                    featurizer_outputs.add(
                        f"{ingredient} share in {predictor.input_descriptor.key}"
                    )
            elif isinstance(predictor, LabelFractionsPredictor):
                for label in predictor.labels:
                    featurizer_outputs.add(
                        f"{label} share in {predictor.input_descriptor.key}"
                    )
            elif isinstance(predictor, (SimpleMixturePredictor, ChemicalFormulaFeaturizer,
                                        MolecularStructureFeaturizer)):
                pass
            else:
                # IngredientsToFormulationRelation, ExpressionPredictor,
                # IngredientsToFormulationPredictor
                raise NotImplementedError(f"Unhandled predictor type: {type(predictor)}")

        output_accumulator = AttributeAccumulationPredictor(
            name="Output variable accumulation",
            description="Output variables encountered in the material history. "
                        "Only sequential mixing steps are considered.",
            attributes=list(automl_outputs.values()),
            sequential=True
        )
        input_accumulator = AttributeAccumulationPredictor(
            name="Attribute accumulation",
            description="Parameters/conditions encountered in the material history. "
                        "Most recent values are selected first.",
            attributes=[automl_inputs[key] for key in automl_inputs
                        if key not in featurizer_outputs],
            sequential=False
        )

        update = GraphPredictor(
            name=self.name,
            description=self.description,
            predictors=self.predictors + [output_accumulator, input_accumulator],
            training_data=self.training_data
        )
        update.uid = self.uid

        return update

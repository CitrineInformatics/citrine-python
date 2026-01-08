"""Resources that represent both individual and collections of workflow executions."""

from deprecation import deprecated
from typing import Iterator, Optional, Union
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.workflows import PredictorEvaluationWorkflow
from citrine.resources.response import Response


class PredictorEvaluationWorkflowCollection(Collection[PredictorEvaluationWorkflow]):
    """A collection of PredictorEvaluationWorkflows."""

    _path_template = "/projects/{project_id}/predictor-evaluation-workflows"
    _individual_key = None
    _collection_key = "response"
    _resource = PredictorEvaluationWorkflow

    @deprecated(
        deprecated_in="3.23.0",
        removed_in="4.0.0",
        details="Predictor evaluation workflows are being eliminated in favor of directly"
        "evaluating predictors. Please use Project.predictor_evaluations instead.",
    )
    def __init__(self, project_id: UUID, session: Session):
        self.project_id: UUID = project_id
        self.session: Session = session

    def build(self, data: dict) -> PredictorEvaluationWorkflow:
        """Build an individual PredictorEvaluationExecution."""
        workflow = PredictorEvaluationWorkflow.build(data)
        workflow._session = self.session
        workflow.project_id = self.project_id
        return workflow

    @deprecated(
        deprecated_in="3.23.0",
        removed_in="4.0.0",
        details="Please use PredictorEvaluations instead, which doesn't store workflows.",
    )
    def archive(self, uid: Union[UUID, str]):
        """Archive a predictor evaluation workflow.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the workflow to archive

        """
        return self._put_resource_ref("archive", uid)

    @deprecated(
        deprecated_in="3.23.0",
        removed_in="4.0.0",
        details="Please use PredictorEvaluations instead, which doesn't store workflows.",
    )
    def restore(self, uid: Union[UUID, str] = None):
        """Restore an archived predictor evaluation workflow.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the workflow to restore

        """
        return self._put_resource_ref("restore", uid)

    @deprecated(deprecated_in="3.23.0", removed_in="4.0.0")
    def delete(self, uid: Union[UUID, str]) -> Response:
        """Predictor Evaluation Workflows cannot be deleted; they can be archived instead."""
        raise NotImplementedError(
            "Predictor Evaluation Workflows cannot be deleted; they can be archived instead."
        )

    @deprecated(
        deprecated_in="3.23.0",
        removed_in="4.0.0",
        details="Please use PredictorEvaluations.trigger_default instead. It doesn't store"
        " a workflow, but it triggers an evaluation with the default evaluators.",
    )
    def create_default(
        self, *, predictor_id: UUID, predictor_version: Optional[Union[int, str]] = None
    ) -> PredictorEvaluationWorkflow:
        """Create a default predictor evaluation workflow for a predictor and execute it.

        The current default predictor evaluation workflow performs 5-fold, 1-trial cross-validation
        on all valid predictor responses. Valid responses are those that are **not** produced by the
        following predictors:

        * :class:`~citrine.informatics.predictors.generalized_mean_property_predictor.GeneralizedMeanPropertyPredictor`
        * :class:`~citrine.informatics.predictors.mean_property_predictor.MeanPropertyPredictor`
        * :class:`~citrine.informatics.predictors.ingredient_fractions_predictor.IngredientFractionsPredictor`
        * :class:`~citrine.informatics.predictors.ingredients_to_simple_mixture_predictor.IngredientsToSimpleMixturePredictor`
        * :class:`~citrine.informatics.predictors.ingredients_to_formulation_predictor.IngredientsToFormulationPredictor`
        * :class:`~citrine.informatics.predictors.label_fractions_predictor.LabelFractionsPredictor`
        * :class:`~citrine.informatics.predictors.molecular_structure_featurizer.MolecularStructureFeaturizer`
        * :class:`~citrine.informatics.predictors.simple_mixture_predictor.SimpleMixturePredictor`

        If there are no valid responses, a default workflow is not created.

        Parameters
        ----------
        predictor_id: UUID
            Unique identifier of the predictor used to create a default workflow
        predictor_version: Option[Union[int, str]]
            The version of the predictor used to create a default workflow

        Returns
        -------
        PredictorEvaluationWorkflow
            Default workflow

        """  # noqa: E501,W505
        url = self._get_path("default")
        payload = {"predictor_id": str(predictor_id)}
        if predictor_version:
            payload["predictor_version"] = predictor_version
        data = self.session.post_resource(url, payload)
        return self.build(data)

    @deprecated(
        deprecated_in="3.23.0",
        removed_in="4.0.0",
        details="Please use PredictorEvaluations instead, which doesn't store workflows.",
    )
    def register(
        self, model: PredictorEvaluationWorkflow
    ) -> PredictorEvaluationWorkflow:
        """Create a new element of the collection by registering an existing resource."""
        return super().register(model)

    @deprecated(
        deprecated_in="3.23.0",
        removed_in="4.0.0",
        details="Please use PredictorEvaluations instead, which doesn't store workflows.",
    )
    def list(self, *, per_page: int = 100) -> Iterator[PredictorEvaluationWorkflow]:
        """Paginate over the elements of the collection."""
        return super().list(per_page=per_page)

    @deprecated(
        deprecated_in="3.23.0",
        removed_in="4.0.0",
        details="Please use PredictorEvaluations instead, which doesn't store workflows.",
    )
    def update(self, model: PredictorEvaluationWorkflow) -> PredictorEvaluationWorkflow:
        """Update a particular element of the collection."""
        return super().update(model)

    @deprecated(
        deprecated_in="3.23.0",
        removed_in="4.0.0",
        details="Please use PredictorEvaluations instead, which doesn't store workflows.",
    )
    def get(self, uid: Union[UUID, str]) -> PredictorEvaluationWorkflow:
        """Get a particular element of the collection."""
        return super().get(uid)

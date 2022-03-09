"""Resources that represent both individual and collections of workflow executions."""
from typing import Union
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine._utils.functions import migrate_deprecated_argument
from citrine.informatics.workflows import PredictorEvaluationWorkflow
from citrine.resources.response import Response


class PredictorEvaluationWorkflowCollection(Collection[PredictorEvaluationWorkflow]):
    """A collection of PredictorEvaluationWorkflows."""

    _path_template = '/projects/{project_id}/predictor-evaluation-workflows'
    _individual_key = None
    _collection_key = 'response'
    _resource = PredictorEvaluationWorkflow

    def __init__(self, project_id: UUID, session: Session):
        self.project_id: UUID = project_id
        self.session: Session = session

    def build(self, data: dict) -> PredictorEvaluationWorkflow:
        """Build an individual PredictorEvaluationExecution."""
        workflow = PredictorEvaluationWorkflow.build(data)
        workflow._session = self.session
        workflow.project_id = self.project_id
        return workflow

    def archive(self, uid: Union[UUID, str] = None, workflow_id: Union[UUID, str] = None):
        """Archive a predictor evaluation workflow.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the workflow to archive
        workflow_id: Union[UUID, str]
            [DEPRECATED] please use uid instead

        """
        uid = migrate_deprecated_argument(uid, "uid", workflow_id, "workflow_id")
        return self._put_resource_ref('archive', uid)

    def restore(self, uid: Union[UUID, str] = None, workflow_id: Union[UUID, str] = None):
        """Restore an archived predictor evaluation workflow.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the workflow to restore
        workflow_id: Union[UUID, str]
            [DEPRECATED] please use uid instead

        """
        uid = migrate_deprecated_argument(uid, "uid", workflow_id, "workflow_id")
        return self._put_resource_ref('restore', uid)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Predictor Evaluation Workflows cannot be deleted; they can be archived instead."""
        raise NotImplementedError(
            "Predictor Evaluation Workflows cannot be deleted; they can be archived instead.")

    def create_default(self, *, predictor_id: UUID) -> PredictorEvaluationWorkflow:
        """[ALPHA] Create a default predictor evaluation workflow for a predictor and execute it.

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

        Returns
        -------
        PredictorEvaluationWorkflow
            Default workflow

        """  # noqa: E501,W505
        url = self._get_path('default')
        payload = {'predictor_id': str(predictor_id)}
        data = self.session.post_resource(url, payload)
        return self.build(data)

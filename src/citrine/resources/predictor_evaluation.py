from functools import partial
from typing import Iterable, Iterator, List, Optional, Union
from uuid import UUID

from citrine.informatics.executions.predictor_evaluation import (
    PredictorEvaluation,
    PredictorEvaluationRequest,
    PredictorEvaluatorsResponse,
)
from citrine.informatics.predictor_evaluator import PredictorEvaluator
from citrine.informatics.predictors import GraphPredictor
from citrine.resources.predictor import LATEST_VER as LATEST_PRED_VER
from citrine._rest.collection import Collection
from citrine._rest.resource import PredictorRef
from citrine._session import Session


class PredictorEvaluationCollection(Collection[PredictorEvaluation]):
    """Represents the collection of predictor evaluations.

    Parameters
    ----------
    project_id: UUID
        the UUID of the project

    """

    _api_version = "v1"
    _path_template = "/projects/{project_id}/predictor-evaluations"
    _individual_key = None
    _resource = PredictorEvaluation
    _collection_key = "response"

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> PredictorEvaluation:
        """Build an individual predictor evaluation."""
        evaluation = PredictorEvaluation.build(data)
        evaluation._session = self.session
        evaluation.project_id = self.project_id
        return evaluation

    def _list_base(
        self,
        *,
        per_page: int = 100,
        predictor_id: Optional[UUID] = None,
        predictor_version: Optional[Union[int, str]] = None,
        archived: Optional[bool] = None,
    ) -> Iterator[PredictorEvaluation]:
        params = {"archived": archived}
        if predictor_id is not None:
            params["predictor_id"] = str(predictor_id)
        if predictor_version is not None:
            params["predictor_version"] = predictor_version

        fetcher = partial(self._fetch_page, additional_params=params)
        return self._paginator.paginate(
            page_fetcher=fetcher,
            collection_builder=self._build_collection_elements,
            per_page=per_page,
        )

    def list_all(
        self,
        *,
        per_page: int = 100,
        predictor_id: Optional[UUID] = None,
        predictor_version: Optional[Union[int, str]] = None,
    ) -> Iterable[PredictorEvaluation]:
        """List all predictor evaluations."""
        return self._list_base(
            per_page=per_page,
            predictor_id=predictor_id,
            predictor_version=predictor_version,
        )

    def list(
        self,
        *,
        per_page: int = 100,
        predictor_id: Optional[UUID] = None,
        predictor_version: Optional[Union[int, str]] = None,
    ) -> Iterable[PredictorEvaluation]:
        """List non-archived predictor evaluations."""
        return self._list_base(
            per_page=per_page,
            predictor_id=predictor_id,
            predictor_version=predictor_version,
            archived=False,
        )

    def list_archived(
        self,
        *,
        per_page: int = 100,
        predictor_id: Optional[UUID] = None,
        predictor_version: Optional[Union[int, str]] = None,
    ) -> Iterable[PredictorEvaluation]:
        """List archived predictor evaluations."""
        return self._list_base(
            per_page=per_page,
            predictor_id=predictor_id,
            predictor_version=predictor_version,
            archived=True,
        )

    def archive(self, uid: Union[UUID, str]):
        """Archive an evaluation."""
        url = self._get_path(uid, action="archive")
        result = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(result)

    def restore(self, uid: Union[UUID, str]):
        """Restore an archived evaluation."""
        url = self._get_path(uid, action="restore")
        result = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(result)

    def default_from_config(self, config: GraphPredictor) -> List[PredictorEvaluator]:
        """Retrieve the default evaluators for an arbitrary (but valid) predictor config.

        See :func:`~citrine.resources.PredictorEvaluationCollection.default` for details
        on the resulting evaluators.
        """
        path = self._get_path(action="default-from-config")
        payload = config.dump()["instance"]
        result = self.session.post_resource(
            path, json=payload, version=self._api_version
        )
        return PredictorEvaluatorsResponse.build(result).evaluators

    def default(
        self,
        *,
        predictor_id: Union[UUID, str],
        predictor_version: Union[int, str] = LATEST_PRED_VER,
    ) -> List[PredictorEvaluator]:
        """Retrieve the default evaluators for a stored predictor.

        The current default evaluators perform 5-fold, 3-trial cross-validation on all valid
        predictor responses. Valid responses are those that are **not** produced by the
        following predictors:

        * :class:`~citrine.informatics.predictors.generalized_mean_property_predictor.GeneralizedMeanPropertyPredictor`
        * :class:`~citrine.informatics.predictors.mean_property_predictor.MeanPropertyPredictor`
        * :class:`~citrine.informatics.predictors.ingredient_fractions_predictor.IngredientFractionsPredictor`
        * :class:`~citrine.informatics.predictors.ingredients_to_simple_mixture_predictor.IngredientsToSimpleMixturePredictor`
        * :class:`~citrine.informatics.predictors.ingredients_to_formulation_predictor.IngredientsToFormulationPredictor`
        * :class:`~citrine.informatics.predictors.label_fractions_predictor.LabelFractionsPredictor`
        * :class:`~citrine.informatics.predictors.molecular_structure_featurizer.MolecularStructureFeaturizer`
        * :class:`~citrine.informatics.predictors.simple_mixture_predictor.SimpleMixturePredictor`

        Parameters
        ----------
        predictor_id: UUID
            Unique identifier of the predictor to evaluate
        predictor_version: Option[Union[int, str]]
            The version of the predictor to evaluate

        Returns
        -------
        PredictorEvaluation

        """  # noqa: E501,W505
        path = self._get_path(action="default")
        payload = PredictorRef(uid=predictor_id, version=predictor_version).dump()
        result = self.session.post_resource(
            path, json=payload, version=self._api_version
        )
        return PredictorEvaluatorsResponse.build(result).evaluators

    def trigger(
        self,
        *,
        predictor_id: Union[UUID, str],
        predictor_version: Union[int, str] = LATEST_PRED_VER,
        evaluators: List[PredictorEvaluator],
    ) -> PredictorEvaluation:
        """Evaluate a predictor using the provided evaluators.

        Parameters
        ----------
        predictor_id: UUID
            Unique identifier of the predictor to evaluate
        predictor_version: Option[Union[int, str]]
            The version of the predictor to evaluate. Defaults to the latest trained version.
        evaluators: List[PredictorEvaluator]
            The evaluators to use to measure predictor performance.

        Returns
        -------
        PredictorEvaluation

        """
        path = self._get_path("trigger")
        payload = PredictorEvaluationRequest(
            evaluators=evaluators,
            predictor_id=predictor_id,
            predictor_version=predictor_version,
        ).dump()
        result = self.session.post_resource(path, payload, version=self._api_version)
        return self.build(result)

    def trigger_default(
        self,
        *,
        predictor_id: Union[UUID, str],
        predictor_version: Union[int, str] = LATEST_PRED_VER,
    ) -> PredictorEvaluation:
        """Evaluate a predictor using the default evaluators.

        See :func:`~citrine.resources.PredictorCollection.default` for details on the evaluators.

        Parameters
        ----------
        predictor_id: UUID
            Unique identifier of the predictor to evaluate
        predictor_version: Option[Union[int, str]]
            The version of the predictor to evaluate

        Returns
        -------
        PredictorEvaluation

        """  # noqa: E501,W505
        path = self._get_path("trigger-default")
        payload = PredictorRef(uid=predictor_id, version=predictor_version).dump()
        result = self.session.post_resource(
            path, json=payload, version=self._api_version
        )
        return self.build(result)

    def register(self, model: PredictorEvaluation) -> PredictorEvaluation:
        """Cannot register an evaluation."""
        raise NotImplementedError("Cannot register a PredictorEvaluation.")

    def update(self, model: PredictorEvaluation) -> PredictorEvaluation:
        """Cannot update an evaluation."""
        raise NotImplementedError("Cannot update a PredictorEvaluation.")

    def delete(self, uid: Union[UUID, str]):
        """Cannot delete an evaluation."""
        raise NotImplementedError("Cannot delete a PredictorEvaluation.")

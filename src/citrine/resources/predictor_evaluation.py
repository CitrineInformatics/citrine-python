"""Resources that represent both individual and collections of predictor evaluation executions."""
from functools import partial
from typing import Optional, Union, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import PredictorRef
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.informatics.executions.predictor_evaluation import PredictorEvaluation
from citrine.resources.response import Response


class PredictorEvaluationCollection(Collection["PredictorEvaluation"]):
    """A collection of PredictorEvaluations."""

    _path_template = '/projects/{project_id}/predictor-evaluation-executions'  # noqa
    _individual_key = None
    _collection_key = 'response'
    _resource = PredictorEvaluation

    def __init__(self, project_id: UUID, session: Session):
        self.project_id: UUID = project_id
        self.session: Session = session

    def build(self, data: dict) -> PredictorEvaluation:
        """Build an individual PredictorEvaluation."""
        evaluation = PredictorEvaluation.build(data)
        evaluation._session = self.session
        evaluation.project_id = self.project_id
        return evaluation
    
    def evaluate(self,
                 uid: Union[UUID, str],
                 *,
                 version: Union[int, str],
                 evaluators: List[PredictorEvaluator]) -> PredictorEvaluation:
        """Evaluate a predictor using the provided evaluators.

        Parameters
        ----------
        predictor_id: UUID
            Unique identifier of the predictor to evaluate
        predictor_version: Option[Union[int, str]]
            The version of the predictor to evaluate. Defaults to the latest trained version.
        evaluators: list

        Returns
        -------
        PredictorEvaluation

        """
        path = self._construct_path(uid, version, "evaluate")
        payload = EvaluatorsPayload(evaluators=evaluators).dump()
        response = self.session.post_resource(path, payload, version=self._api_version)
        return self._build_predictor_evaluation(response)

    def evaluate_default(self,
                         uid: Union[UUID, str],
                         *,
                         version: Union[int, str]) -> PredictorEvaluation:
        """Evaluate a predictor using the default evaluators.

        See :func:`~citrine.resources.PredictorCollection.default_evaluators` for details on the evaluators.

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
        return self._versions_collection.evaluate_default(uid, version=version)
        path = self._construct_path(uid, version, "evaluate-default")
        response = self.session.post_resource(path, {}, version=self._api_version)
        return self._build_predictor_evaluation(response)

    def register(self, model: PredictorEvaluation) -> PredictorEvaluation:
        """Cannot register an evaluation."""
        raise NotImplementedError("Cannot register a PredictorEvaluation.")

    def update(self, model: PredictorEvaluation) -> PredictorEvaluation:
        """Cannot update an evaluation."""
        raise NotImplementedError("Cannot update a PredictorEvaluation.")

    def archive(self, uid: Union[UUID, str]):
        """Cannot archive an evaluation."""
        raise NotImplementedError("Cannot update a PredictorEvaluation.")

    def restore(self, uid: Union[UUID, str]):
        """Cannot restore an evaluation."""
        raise NotImplementedError("Cannot update a PredictorEvaluation.")

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Cannot delete an evaluation."""
        raise NotImplementedError("Cannot delete a PredictorEvaluation.")

    def list(self,
             *,
             per_page: int = 100,
             predictor_id: Optional[UUID] = None,
             predictor_version: Optional[Union[int, str]] = None
             ) -> Iterator[PredictorEvaluation]:
        """
        Paginate over predictor evaluations.

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. Default is 100.
        predictor_id: uuid, optional
            list evaluations that targeted the predictor with this id
        predictor_version: Union[int, str], optional
            list evaluations that targeted the predictor with this version

        Returns
        -------
        Iterator[PredictorEvaluation]
            The matching predictor evaluations.

        """
        params = {}
        if predictor_id is not None:
            params["predictor_id"] = str(predictor_id)
        if predictor_version is not None:
            params["predictor_version"] = predictor_version

        fetcher = partial(self._fetch_page, additional_params=params)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

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

    def trigger(self,
                predictor_id: UUID,
                *,
                predictor_version: Optional[Union[int, str]] = None,
                random_state: Optional[int] = None):
        """Trigger a predictor evaluation execution against a predictor.

        Parameters
        -----------
        predictor_id: UUID
            ID of the predictor to evaluate.
        predictor_version: Union[int, str], optional
            The version of the predictor to evaluate.
        random_state: int, optional
            Seeds the evaluators' random number generator so that the results are repeatable.

        """
        if self.workflow_id is None:
            msg = "Cannot trigger a predictor evaluation execution without knowing the " \
                  "predictor evaluation workflow. Use workflow.executions.trigger instead of " \
                  "project.predictor_evaluation_executions.trigger"
            raise RuntimeError(msg)
        path = format_escaped_url(
            '/projects/{project_id}/predictor-evaluation-workflows/{workflow_id}/executions',
            project_id=self.project_id,
            workflow_id=self.workflow_id
        )

        params = dict()
        if random_state is not None:
            params["random_state"] = random_state

        payload = PredictorRef(predictor_id, predictor_version).dump()
        data = self.session.post_resource(path, payload, params=params, version='v2')

        return self.build(data)

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

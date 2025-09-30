from functools import lru_cache
from typing import List, Optional, Union
from uuid import UUID

from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult
from citrine.informatics.predictor_evaluator import PredictorEvaluator
from citrine.resources.status_detail import StatusDetail
from citrine._rest.engine_resource import EngineResourceWithoutStatus
from citrine._rest.resource import PredictorRef
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._utils.functions import format_escaped_url


class PredictorEvaluatorsResponse(Serializable['EvaluatorsPayload']):
    """Container object for a default predictor evaluator response."""

    evaluators = properties.List(properties.Object(PredictorEvaluator), "evaluators")

    def __init__(self, evaluators: List[PredictorEvaluator]):
        self.evaluators = evaluators


class PredictorEvaluationRequest(Serializable['EvaluatorsPayload']):
    """Container object for a predictor evaluation request."""

    predictor = properties.Object(PredictorRef, "predictor")
    evaluators = properties.List(properties.Object(PredictorEvaluator), "evaluators")

    def __init__(self,
                 *,
                 evaluators: List[PredictorEvaluator],
                 predictor_id: Union[UUID, str],
                 predictor_version: Optional[Union[int, str]] = None):
        self.evaluators = evaluators
        self.predictor = PredictorRef(predictor_id, predictor_version)


class PredictorEvaluation(EngineResourceWithoutStatus['PredictorEvaluation']):
    """The evaluation of a predictor's performance."""

    uid: UUID = properties.UUID('id', serializable=False)
    """:UUID: Unique identifier of the evaluation"""
    evaluators = properties.List(properties.Object(PredictorEvaluator), "data.evaluators",
                                 serializable=False)
    """:List{PredictorEvaluator]:the predictor evaluators that were executed. These are used
    when calling the ``results()`` method."""
    predictor_id = properties.UUID('metadata.predictor_id', serializable=False)
    """:UUID:"""
    predictor_version = properties.Integer('metadata.predictor_version', serializable=False)
    status = properties.String('metadata.status.major', serializable=False)
    """:str: short description of the evaluation's status"""
    status_description = properties.String('metadata.status.minor', serializable=False)
    """:str: more detailed description of the evaluation's status"""
    status_detail = properties.List(properties.Object(StatusDetail), 'metadata.status.detail',
                                    default=[], serializable=False)
    """:List[StatusDetail]: a list of structured status info, containing the message and level"""

    def _path(self):
        return format_escaped_url(
            '/projects/{project_id}/predictor-evaluations/{evaluation_id}',
            project_id=str(self.project_id),
            evaluation_id=str(self.uid)
        )

    @lru_cache()
    def results(self, evaluator_name: str) -> PredictorEvaluationResult:
        """
        Get a specific evaluation result by the name of the evaluator that produced it.

        Parameters
        ----------
        evaluator_name: str
            Name of the evaluator for which to get the results

        Returns
        -------
        PredictorEvaluationResult
            The evaluation result from the evaluator with the given name

        """
        params = {"evaluator_name": evaluator_name}
        resource = self._session.get_resource(self._path() + "/results", params=params)
        return PredictorEvaluationResult.build(resource)

    @property
    def evaluator_names(self):
        """Names of the predictor evaluators. Used when calling the ``results()`` method."""
        return list(iter(self))

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.results(item)
        else:
            raise TypeError("Results are accessed by string names")

    def __iter__(self):
        return iter(e.name for e in self.evaluators)

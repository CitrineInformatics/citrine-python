from functools import lru_cache

from citrine.informatics.executions.execution import Execution
from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult
from citrine.informatics.predictor_evaluator import PredictorEvaluator
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._utils.functions import format_escaped_url


class PredictorEvaluation(Resource['PredictorEvaluation'], Execution):
    """The evaluation of a predictor's performance.

    Possible statuses are INPROGRESS, SUCCEEDED, and FAILED.
    Predictor evaluation executions also have a ``status_description`` field with more information.

    """

    evaluators = properties.List(properties.Object(PredictorEvaluator), "evaluators",
                                 serializable=False)
    """:List{PredictorEvaluator]:the predictor evaluators that were executed. These are used
    when calling the ``results()`` method."""
    workflow_id = properties.UUID('workflow_id', serializable=False)
    """:UUID: Unique identifier of the workflow that was executed"""
    predictor_id = properties.UUID('predictor_id', serializable=False)
    predictor_version = properties.Integer('predictor_version', serializable=False)

    def _path(self):
        return format_escaped_url(
            '/projects/{project_id}/predictor-evaluation-executions/{execution_id}',
            project_id=str(self.project_id),
            execution_id=str(self.uid)
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

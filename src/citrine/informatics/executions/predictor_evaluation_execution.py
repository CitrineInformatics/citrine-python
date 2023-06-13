from functools import lru_cache

from citrine._serialization import properties
from citrine._utils.functions import format_escaped_url
from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult
from citrine.informatics.executions.execution import Execution
from citrine._rest.resource import Resource


class PredictorEvaluationExecution(Resource['PredictorEvaluationExecution'], Execution):
    """The execution of a PredictorEvaluationWorkflow.

    Possible statuses are INPROGRESS, SUCCEEDED, and FAILED.
    Predictor evaluation executions also have a ``status_description`` field with more information.

    """

    evaluator_names = properties.List(properties.String, "evaluator_names", serializable=False)
    """:List[str]: names of the predictor evaluators that were executed. These are used
    when calling the ``results()`` method."""
    workflow_id = properties.UUID('workflow_id', serializable=False)
    """:UUID: Unique identifier of the workflow that was executed"""
    predictor_id = properties.UUID('predictor_id', serializable=False)
    predictor_version = properties.Integer('predictor_version', serializable=False)

    def _path(self):
        return format_escaped_url(
            '/projects/{project_id}/predictor-evaluation-executions/{execution_id}',
            project_id=self.project_id,
            execution_id=self.uid
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

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.results(item)
        else:
            raise TypeError("Results are accessed by string names")

    def __iter__(self):
        return iter(self.evaluator_names)

from functools import lru_cache
from typing import List, Optional
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult
from citrine.resources.status_detail import StatusDetail

from deprecation import deprecated


class PredictorEvaluationExecution(Resource['PredictorEvaluationExecution'], AsynchronousObject):
    """The execution of a PredictorEvaluationWorkflow.

    Possible statuses are INPROGRESS, SUCCEEDED, and FAILED.
    Predictor evaluation executions also have a ``status_description`` field with more information.

    """

    _session: Optional[Session] = None
    _in_progress_statuses = ["INPROGRESS"]
    _succeeded_statuses = ["SUCCEEDED"]
    _failed_statuses = ["FAILED"]
    project_id: Optional[UUID] = None
    """:Optional[UUID]: Unique ID of the project that contains this execution."""

    uid: UUID = properties.UUID('id', serializable=False)
    """:UUID: Unique identifier of the workflow execution"""
    evaluator_names = properties.List(properties.String, "evaluator_names", serializable=False)
    """:List[str]: names of the predictor evaluators that were executed. These are used
    when calling the ``results()`` method."""
    workflow_id = properties.UUID('workflow_id', serializable=False)
    """:UUID: Unique identifier of the workflow that was executed"""
    predictor_id = properties.UUID('predictor_id', serializable=False)
    predictor_version = properties.Integer('predictor_version', serializable=False)
    status = properties.Optional(properties.String(), 'status', serializable=False)
    """:Optional[str]: short description of the execution's status"""
    status_detail = properties.List(properties.Object(StatusDetail), 'status_detail', default=[],
                                    serializable=False)
    """:List[StatusDetail]: a list of structured status info, containing the message and level"""

    @property
    @deprecated(deprecated_in="2.2.0", removed_in="3.0.0", details="Use status_detail instead.")
    def status_info(self) -> List[str]:
        """:List[str]: human-readable explanations of the status."""
        return [detail.msg for detail in self.status_detail]

    def __init__(self):
        """Predictor evaluation executions are not directly instantiated by the user."""
        pass  # pragma: no cover

    def __str__(self):
        return '<PredictorEvaluationExecution {!r}>'.format(str(self.uid))

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

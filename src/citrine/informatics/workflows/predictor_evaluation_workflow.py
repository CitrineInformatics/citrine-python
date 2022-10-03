from typing import List

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine.informatics.predictor_evaluator import PredictorEvaluator
from citrine.informatics.workflows.workflow import Workflow
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecutionCollection
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['PredictorEvaluationWorkflow']


class PredictorEvaluationWorkflow(Resource['PredictorEvaluationWorkflow'],
                                  Workflow, AIResourceMetadata):
    """A workflow that evaluations a predictor.

    Parameters
    ----------
    name: str
        name of the predictor evaluation workflow
    description: str
        the description of the predictor evaluation workflow
    evaluators: List[PredictorEvaluator]
        the list of evaluators to apply to the predictor

    """

    evaluators = properties.List(properties.Object(PredictorEvaluator), "evaluators")

    status_description = properties.String('status_description', serializable=False)
    """:str: more detailed description of the workflow's status"""
    typ = properties.String('type', default='PredictorEvaluationWorkflow', deserializable=False)

    _resource_type = ResourceTypeEnum.MODULE

    def __init__(self,
                 name: str,
                 *,
                 description: str = "",
                 evaluators: List[PredictorEvaluator]):
        self.name: str = name
        self.description: str = description
        self.evaluators: List[PredictorEvaluator] = evaluators

    def __str__(self):
        return '<PredictorEvaluationWorkflow {!r}>'.format(self.name)

    @property
    def executions(self) -> PredictorEvaluationExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return PredictorEvaluationExecutionCollection(
            project_id=self.project_id, session=self._session, workflow_id=self.uid)

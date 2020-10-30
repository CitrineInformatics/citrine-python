"""Tools for working with design workflows."""
from typing import Type

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable


__all__ = ['Workflow']


class Workflow(PolymorphicSerializable['Workflow']):
    """[ALPHA] A Citrine Workflow is a collection of Modules that together accomplish some task.

    Abstract type that returns the proper type given a serialized dict.

    """

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type['Workflow']:
        """Return the subtype."""
        from .design_workflow import DesignWorkflow
        from .performance_workflow import PerformanceWorkflow
        from .predictor_evaluation_workflow import PredictorEvaluationWorkflow
        type_dict = {
            'DESIGN_WORKFLOW': DesignWorkflow,
            'PERFORMANCE_WORKFLOW': PerformanceWorkflow,
            'PREDICTOR_EVALUATION_WORKFLOW': PredictorEvaluationWorkflow,
        }
        typ = type_dict.get(data['module_type'])

        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid workflow type. '
                'Must be in {}.'.format(data['module_type'], type_dict.keys())
            )

"""Tools for working with Citrine Informatics functionality."""
from citrine.informatics.design_spaces import DesignSpace
from citrine.informatics.executions import PredictorEvaluationExecution, DesignExecution
from citrine.informatics.predictors import Predictor
from citrine.informatics.processors import Processor
from citrine.informatics.workflows import DesignWorkflow, PredictorEvaluationWorkflow
from citrine.resources import ProjectCollection


def fetch(entity):
    """Fetch and return an updated version of the resource."""
    if entity._session is None or entity._project_id is None:
        raise ValueError("Can only call 'updated' on a resource that was previously returned by 'get' or 'register'.")

    project = ProjectCollection(entity._session).get(entity._project_id)
    if isinstance(entity, Predictor):
        return project.predictors.get(entity.uid)
    elif isinstance(entity, DesignSpace):
        return project.design_spaces.get(entity.uid)
    elif isinstance(entity, Processor):
        return project.processors.get(entity.uid)
    elif isinstance(entity, DesignWorkflow):
        return project.design_workflows.get(entity.uid)
    elif isinstance(entity, PredictorEvaluationWorkflow):
        return project.predictor_evaluation_workflows.get(entity.uid)
    elif isinstance(entity, PredictorEvaluationExecution):
        return project.predictor_evaluation_executions.get(entity.uid)
    elif isinstance(entity, DesignExecution):
        return project.design_workflows.get(entity.workflow_id).design_executions.get(entity.uid)


def status(entity):
    """Fetch and return the status of the resource."""
    return fetch(entity).status


def status_info(entity):
    """Fetch and return the status_info of the resource."""
    return fetch(entity).status_info


def status_description(entity):
    """Fetch and return the status_description of the resource."""
    return fetch(entity).status_description

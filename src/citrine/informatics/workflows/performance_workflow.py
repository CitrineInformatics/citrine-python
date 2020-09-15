from typing import Optional
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.informatics.analysis_configuration import CrossValidationAnalysisConfiguration
from citrine.informatics.workflows.workflow import Workflow
from citrine.resources.workflow_executions import WorkflowExecutionCollection

__all__ = ['PerformanceWorkflow']


class PerformanceWorkflow(Resource['PerformanceWorkflow'], Workflow):
    """[ALPHA] Object that executes performance analysis on a given module.

    Parameters
    ----------
    name: str
        the name of the workflow
    analysis: CrossValidationAnalysisConfiguration
        the configuration object

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('display_name')
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    experimental = properties.Boolean("experimental", serializable=False, default=True)
    experimental_reasons = properties.Optional(
        properties.List(properties.String()),
        'experimental_reasons',
        serializable=False
    )
    active = properties.Boolean('active', default=True)
    archived = properties.Boolean('archived', default=False)
    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)
    analysis = properties.Object(CrossValidationAnalysisConfiguration, 'config.analysis')
    module_type = properties.String('module_type', default='PERFORMANCE_WORKFLOW')
    schema_id = properties.UUID('schema_id', default=UUID('1d213f0a-d07c-4f70-a4d0-bda3aa951ee0'))
    typ = properties.String('config.type', default='PerformanceWorkflow', deserializable=False)

    def __init__(self,
                 name: str,
                 analysis: CrossValidationAnalysisConfiguration,
                 project_id: Optional[UUID] = None,
                 session: Session = Session()):
        self.name = name
        self.analysis = analysis
        self.project_id = project_id
        self.session = session

    def __str__(self):
        return '<PerformanceWorkflow {!r}>'.format(self.name)

    @property
    def executions(self) -> WorkflowExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return WorkflowExecutionCollection(self.project_id, self.uid, self.session)

"""Tools for working with design workflows."""
from typing import Type, Optional
from uuid import UUID

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties
from citrine._rest.resource import Resource
from citrine._session import Session
from citrine.resources.workflow_executions import WorkflowExecutionCollection
from citrine.informatics.analysis_configuration import CrossValidationAnalysisConfiguration

__all__ = ['Workflow', 'DesignWorkflow', 'PerformanceWorkflow']


class Workflow(PolymorphicSerializable['Workflow']):
    """[ALPHA] A Citrine Workflow is a collection of Modules that together accomplish some task.

    Abstract type that returns the proper type given a serialized dict.


    """

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type['Workflow']:
        """Return the subtype."""
        type_dict = {
            'DESIGN_WORKFLOW': DesignWorkflow,
            'PERFORMANCE_WORKFLOW': PerformanceWorkflow,
        }
        typ = type_dict.get(data['module_type'])

        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid workflow type. '
                'Must be in {}.'.format(data['module_type'], type_dict.keys())
            )


class DesignWorkflow(Resource['DesignWorkflow'], Workflow):
    """[ALPHA] Object that generates scored materials that may approach higher values of the score.

    Parameters
    ----------
    name: str
        the name of the workflow
    design_space_id: UUID
        the UUID corresponding to the design space to use
    processor_id: Optional[UUID]
        the UUID corresponding to the processor to use
        if none is provided, one matching your design space will be automatically generated
    predictor_id: UUID
        the UUID corresponding to the predictor to use
    project_id: UUID
        the UUID corresponding to the project to use

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('display_name')
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    active = properties.Boolean('active', default=True)
    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)
    design_space_id = properties.UUID('config.design_space_id')
    processor_id = properties.Optional(properties.UUID, 'config.processor_id')
    predictor_id = properties.UUID('config.predictor_id')
    module_type = properties.String('module_type', default='DESIGN_WORKFLOW')
    schema_id = properties.UUID('schema_id', default=UUID('8af8b007-3e81-4185-82b2-6f62f4a2e6f1'))

    def __init__(self,
                 name: str,
                 design_space_id: UUID,
                 processor_id: Optional[UUID],
                 predictor_id: UUID,
                 project_id: Optional[UUID] = None,
                 session: Session = Session()):
        self.name = name
        self.design_space_id = design_space_id
        self.processor_id = processor_id
        self.predictor_id = predictor_id
        self.project_id = project_id
        self.session = session

    def __str__(self):
        return '<DesignWorkflow {!r}>'.format(self.name)

    @property
    def executions(self) -> WorkflowExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return WorkflowExecutionCollection(self.project_id, self.uid, self.session)


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
    active = properties.Boolean('active', default=True)
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

from typing import Optional
from uuid import UUID

from deprecation import deprecated
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.informatics.workflows.workflow import Workflow
from citrine.resources.workflow_executions import WorkflowExecutionCollection
from citrine.resources.design_execution import DesignExecutionCollection
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['DesignWorkflow']


class DesignWorkflow(Resource['DesignWorkflow'], Workflow, AIResourceMetadata):
    """Object that generates scored materials that may approach higher values of the score.

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

    # TODO: after PerformanceWorkflows are removed, get rid of this line and also
    #   consolidate common fields in the Workflow object
    name = properties.String('display_name')
    name = properties.String('name')
    description = properties.Optional(properties.String, 'description')

    design_space_id = properties.UUID('design_space_id')
    processor_id = properties.Optional(properties.UUID, 'processor_id')
    predictor_id = properties.UUID('predictor_id')

    status_description = properties.String('status_description', serializable=False)
    """:str: more detailed description of the workflow's status"""

    module_type = properties.String('module_type', default='DESIGN_WORKFLOW')
    typ = properties.String('type', default='DesignWorkflow', deserializable=False)

    def __init__(self,
                 name: str,
                 design_space_id: UUID,
                 processor_id: Optional[UUID],
                 predictor_id: UUID,
                 project_id: Optional[UUID] = None,
                 session: Session = Session(),
                 description: Optional[str] = None):
        self.name = name
        self.design_space_id = design_space_id
        self.processor_id = processor_id
        self.predictor_id = predictor_id
        self.project_id = project_id
        self.session = session
        self.description = description

    def __str__(self):
        return '<DesignWorkflow {!r}>'.format(self.name)

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        """Makes Design Workflows backwards compatible.

        module route used to return info in the `config`
        """
        if 'config' in data:
            # pull config info out of old style workflow
            data['name'] = data['display_name']
            data['status_description'] = data['status']
            data['predictor_id'] = data['config']['predictor_id']
            data['design_space_id'] = data['config']['design_space_id']
            if 'processor_id' in data['config']:
                data['processor_id'] = data['config']['processor_id']
        return data

    def _post_dump(self, data: dict) -> dict:
        """Makes Design Workflows backwards compatible.

        the old module route expects `config` and `display_name`
        """
        data['display_name'] = data['name']
        config = {
            'predictor_id': data['predictor_id'],
            'design_space_id': data['design_space_id'],
            'type': 'DesignWorkflow'  # needs to be added here so it doesn't get overwritten
        }
        if 'processor_id' in data:
            config['processor_id'] = data['processor_id']
        data['config'] = config
        return data

    @property
    @deprecated(deprecated_in="0.101.0",
                details="Use design_executions instead")
    def executions(self) -> WorkflowExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return WorkflowExecutionCollection(self.project_id, self.uid, self.session)

    @property
    def design_executions(self) -> DesignExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return DesignExecutionCollection(
            project_id=self.project_id, session=self.session, workflow_id=self.uid)

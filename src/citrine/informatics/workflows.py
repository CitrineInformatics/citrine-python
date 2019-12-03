"""Tools for working with design workflows."""
from typing import Type, Optional
from uuid import UUID

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties
from citrine._rest.resource import Resource
from citrine._session import Session
from citrine.resources.workflow_executions import WorkflowExecutionCollection

__all__ = ['Workflow', 'DesignWorkflow']


class Workflow(PolymorphicSerializable['Workflow']):
    """A Citrine Workflow is a collection of Modules that together accomplish some task.

    Abstract type that returns the proper type given a serialized dict.


    """

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type['Workflow']:
        """Return the sole currently implemented subtype."""
        return DesignWorkflow


class DesignWorkflow(Resource['DesignWorkflow'], Workflow):
    """Object that generates scored materials that may approach higher values of the score.

    Parameters
    ----------
    name: str
        the name of the workflow
    design_space_id: UUID
        the UUID corresponding to the design space to use
    processor_id: UUID
        the UUID corresponding to the processor to use
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

    # TODO: Figure out how to make these fields richer/use actual objects
    design_space_id = properties.UUID('modules.design_space_id')
    processor_id = properties.UUID('modules.processor_id')
    predictor_id = properties.UUID('modules.predictor_id')

    # The project_id is used to keep a reference to the project under which the workflow was
    # created. It is currently unclear if this is the best way to do this. Another option might
    # be to have all objects have a context object, but that also seems to have downsides.
    def __init__(self,
                 name: str,
                 design_space_id: UUID,
                 processor_id: UUID,
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

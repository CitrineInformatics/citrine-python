from typing import Optional, Union
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine.informatics.workflows.workflow import Workflow
from citrine.resources.design_execution import DesignExecutionCollection
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['DesignWorkflow']


class DesignWorkflow(Resource['DesignWorkflow'], Workflow, AIResourceMetadata):
    """Object that generates scored materials that may approach higher values of the score.

    Parameters
    ----------
    name: str
        the name of the workflow
    design_space_id: Optional[UUID]
        the UUID corresponding to the design space to use
    predictor_id: Optional[UUID]
        the UUID corresponding to the predictor to use
    predictor_version: Optional[Union[int, str]]
        the version of the predictor to use
    description: Optional[str]
        a description of the workflow

    """

    design_space_id = properties.Optional(properties.UUID, 'design_space_id')
    predictor_id = properties.Optional(properties.UUID, 'predictor_id')
    predictor_version = properties.Optional(
        properties.Union([properties.Integer(), properties.String()]), 'predictor_version')
    _branch_id: Optional[UUID] = properties.Optional(properties.UUID, 'branch_id')

    status_description = properties.String('status_description', serializable=False)
    """:str: more detailed description of the workflow's status"""
    typ = properties.String('type', default='DesignWorkflow', deserializable=False)

    _branch_root_id: Optional[UUID] = properties.Optional(properties.UUID, 'branch_root_id',
                                                          serializable=False, deserializable=False)
    """:Optional[UUID]: Root ID of the branch that contains this workflow."""
    _branch_version: Optional[int] = properties.Optional(properties.Integer, 'branch_version',
                                                         serializable=False, deserializable=False)
    """:Optional[int]: Version number of the branch that contains this workflow."""

    def __init__(self,
                 name: str,
                 *,
                 design_space_id: Optional[UUID] = None,
                 predictor_id: Optional[UUID] = None,
                 predictor_version: Optional[Union[int, str]] = None,
                 description: Optional[str] = None):
        self.name = name
        self.design_space_id = design_space_id
        self.predictor_id = predictor_id
        self.predictor_version = predictor_version
        self.description = description

    def __str__(self):
        return '<DesignWorkflow {!r}>'.format(self.name)

    @property
    def design_executions(self) -> DesignExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return DesignExecutionCollection(
            project_id=self.project_id, session=self._session, workflow_id=self.uid)

    @property
    def branch_root_id(self):
        """Retrieve the root ID of the branch this workflow is on."""
        return self._branch_root_id

    @branch_root_id.setter
    def branch_root_id(self, value):
        """Set the root ID of the branch this workflow is on."""
        self._branch_root_id = value
        self._branch_id = None

    @property
    def branch_version(self):
        """Retrieve the version of the branch this workflow is on."""
        return self._branch_version

    @branch_version.setter
    def branch_version(self, value):
        """Set the version of the branch this workflow is on."""
        self._branch_version = value
        self._branch_id = None

from typing import Optional, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.resources.design_workflow import DesignWorkflowCollection


class Branch(Resource['Branch']):
    """
    A project branch.

    A branch is a container for design workflows.
    """

    name = properties.String('name')
    uid = properties.Optional(properties.UUID(), 'id')
    created_at = properties.Optional(properties.Datetime(), 'created_at', serializable=False)
    updated_at = properties.Optional(properties.Datetime(), 'updated_at', serializable=False)

    project_id: Optional[UUID] = None

    def __init__(self,
                 name: str,
                 *,
                 session: Optional[Session] = None):
        self.name: str = name
        self.session: Session = session

    def __str__(self):
        return f'<Branch {self.name!r}>'

    @property
    def design_workflows(self) -> DesignWorkflowCollection:
        """Return a resource representing all workflows contained within this branch."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize workflow without project reference!')
        return DesignWorkflowCollection(project_id=self.project_id,
                                        session=self.session,
                                        branch_id=self.uid)


class BranchCollection(Collection[Branch]):
    """A collection of Branches."""

    _path_template = '/projects/{project_id}/design-workflow-branches'
    _individual_key = None
    _collection_key = 'response'
    _resource = Branch

    def __init__(self, project_id: UUID, session: Session):
        self.project_id: UUID = project_id
        self.session: Session = session

    def build(self, data: dict) -> Branch:
        """
        Build an individual branch from a dictionary.

        Parameters
        ----------
        data: dict
            A dictionary representing the branch.

        Return
        -------
        Branch
            The branch created from data.

        """
        branch = Branch.build(data)
        branch.session = self.session
        branch.project_id = self.project_id
        return branch

    def list(self, *, per_page: int = 20) -> Iterator[Branch]:
        """
        List branches using pagination.

        Yields all elements in the collection, paginating over all available pages.

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. Default is 20.  This parameter
            is used when making requests to the backend service.

        Returns
        -------
        Iterator[Branch]
            Branches in this collection.

        """
        return super().list(per_page=per_page)

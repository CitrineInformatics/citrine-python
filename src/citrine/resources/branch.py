import functools
from typing import Iterator, Optional, Union
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.resources.design_workflow import DesignWorkflowCollection


class Branch(Resource['Branch']):
    """
    A project branch.

    A branch is a container for design workflows.
    """

    name = properties.String('name')
    uid = properties.Optional(properties.UUID(), 'id')
    archived = properties.Boolean('archived', serializable=False)
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
        List active branches using pagination.

        Yields all active branches, paginating over all available pages.

        Parameters
        ---------
        per_page: int, optional
            Max number of branches to return per page. Default is 20. This parameter is used when
            making requests to the backend service.

        Returns
        -------
        Iterator[Branch]
            Active branches in this collection.

        """
        return super().list(per_page=per_page)

    def list_archived(self, *, per_page: int = 20) -> Iterator[Branch]:
        """
        List archived branches using pagination.

        Yields all archived branches, paginating over all available pages.

        Parameters
        ---------
        per_page: int, optional
            Max number of branches to return per page. Default is 20. This parameter is used when
            making requests to the backend service.

        Returns
        -------
        Iterator[Branch]
            Archived branches in this collection.

        """
        fetcher = functools.partial(self._fetch_page, additional_params={"archived": True})
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def archive(self, uid: Union[UUID, str] = None):
        """
        Archive a branch.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the branch to archive

        """
        archive_path_template = f'{self._get_path(uid)}/archive'
        url = format_escaped_url(archive_path_template, project_id=self.project_id, branch_id=uid)
        data = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(data)

    def restore(self, uid: Union[UUID, str] = None):
        """
        Restore an archived branch.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the branch to restore

        """
        restore_path_template = f'{self._get_path(uid)}/restore'
        url = format_escaped_url(restore_path_template, project_id=self.project_id, branch_id=uid)
        data = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(data)

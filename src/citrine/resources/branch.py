import functools
from typing import Iterator, Optional, Union
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.exceptions import NotFound
from citrine.resources.data_version_update import BranchDataUpdate, NextBranchVersionRequest
from citrine.resources.design_workflow import DesignWorkflowCollection
from citrine.resources.experiment_datasource import (ExperimentDataSourceCollection,
                                                     ExperimentDataSource)


LATEST_VER = "latest"  # Refers to the most recently created branch version.


class Branch(Resource['Branch']):
    """
    A project branch.

    A branch is a container for design workflows.
    """

    name = properties.String('data.name')
    uid = properties.Optional(properties.UUID(), 'id')
    archived = properties.Boolean('metadata.archived', serializable=False)
    created_at = properties.Optional(properties.Datetime(), 'metadata.created.time',
                                     serializable=False)
    updated_at = properties.Optional(properties.Datetime(), 'metadata.updated.time',
                                     serializable=False)
    # added in v2
    root_id = properties.UUID('metadata.root_id', serializable=False)
    version = properties.Integer('metadata.version', serializable=False)

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
                                        branch_root_id=self.root_id,
                                        branch_version=self.version)

    @property
    def experiment_datasource(self) -> Optional[ExperimentDataSource]:
        """Return this branch's experiment data source, or None if one doesn't exist."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot retrieve datasource without project reference!')
        erds = ExperimentDataSourceCollection(project_id=self.project_id, session=self.session)
        branch_erds_iter = erds.list(branch_version_id=self.uid, version=LATEST_VER)
        return next(branch_erds_iter, None)

    def _post_dump(self, data: dict) -> dict:
        # Only the data portion of an entity is sent to the server.
        data = data["data"]
        return data


class BranchCollection(Collection[Branch]):
    """A collection of Branches."""

    _path_template = '/projects/{project_id}/branches'
    _individual_key = None
    _collection_key = 'response'
    _resource = Branch
    _api_version = 'v2'

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

    def get(self,
            *,
            root_id: Union[UUID, str],
            version: Optional[Union[int, str]] = LATEST_VER) -> Branch:
        """
        Retrieve a branch by its root ID and, optionally, its version number.

        Omitting the version number will retrieve the latest version.

        Parameters
        ---------
        root_id: Union[UUID, str]
            Unique identifier of the branch root

        version: Union[int, str], optional
            The version of the branch to retrieve. If provided, must either be a positive integer,
            or "latest". Defaults to "latest".

        Returns
        -------
        Branch
            The requested version of the branch.

        """
        version = version or LATEST_VER
        params = {"root": str(root_id), "version": version}
        branch = next(self._list_with_params(per_page=1, **params), None)
        if branch:
            return branch
        else:
            raise NotFound.build(
                message=f"Branch root '{root_id}', version {version} not found",
                method="GET",
                path=self._get_path(),
                params=params
            )

    def get_by_version_id(self, *, version_id: Union[UUID, str]) -> Branch:
        """
        Given a branch version ID, retrieve the branch.

        Parameters
        ---------
        version_id: Union[UUID, str]
            Unique ID of the branch version

        Returns
        -------
        Branch
            The requested branch.

        """
        return super().get(version_id)

    def list(self, *, per_page: int = 20) -> Iterator[Branch]:
        """
        List all active branches using pagination.

        Yields all active branches paginating over all available pages.

        Parameters
        ---------
        per_page: int, optional
            Max number of branches to return per page. Default is 20. This parameter is used when
            making requests to the backend service.

        Returns
        -------
        Iterator[Branch]
            All branches in this collection.

        """
        return self._list_with_params(per_page=per_page, archived=False)

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
        return self._list_with_params(per_page=per_page, archived=True)

    def list_all(self, *, per_page: int = 20) -> Iterator[Branch]:
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
        return self._list_with_params(per_page=per_page)

    def _list_with_params(self, *, per_page, **kwargs):
        fetcher = functools.partial(self._fetch_page, additional_params=kwargs)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def archive(self,
                *,
                root_id: Union[UUID, str],
                version: Optional[Union[int, str]] = LATEST_VER):
        """
        Archive a branch.

        Parameters
        ----------
        root_id: Union[UUID, str]
            Unique ID of the branch root

        version: Union[int, str], optional
            The version of the branch. If provided, must either be a positive integer, or "latest".
            Defaults to "latest".

        """
        version = version or LATEST_VER
        # The backend API at present expects a branch version ID, so we must look it up.
        uid = self.get(root_id=root_id, version=version).uid

        url = self._get_path(uid, action="archive")
        data = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(data)

    def restore(self,
                *,
                root_id: Union[UUID, str],
                version: Optional[Union[int, str]] = LATEST_VER):
        """
        Restore an archived branch.

        Parameters
        ----------
        root_id: Union[UUID, str]
            Unique ID of the branch root

        version: Union[int, str], optional
            The version of the branch. If provided, must either be a positive integer, or "latest".
            Defaults to "latest".

        """
        version = version or LATEST_VER
        # The backend API at present expects a branch version ID, so we must look it up.
        uid = self.get(root_id=root_id, version=version).uid

        url = self._get_path(uid, action="restore")
        data = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(data)

    def update_data(self,
                    *,
                    root_id: Union[UUID, str],
                    version: Optional[Union[int, str]] = LATEST_VER,
                    use_existing: bool = True,
                    retrain_models: bool = False) -> Optional[Branch]:
        """
        Automatically advance the branch to the next version.

        If there are no newer versions of data sources used by this branch this method returns
        without doing anything

        Parameters
        ----------
        root_id: Union[UUID, str]
            Unique ID of the branch root

        version: Union[int, str], optional
            The version of the branch. If provided, must either be a positive integer, or "latest".
            Defaults to "latest".

        use_existing: bool
            If true the workflows in this branch will use existing predictors that are using
            the latest versions of the data sources and are ready to use.

        retrain_models: bool
            If true, when new versions of models are created, they are automatically
            scheduled for training.

        Returns
        -------
        Branch
            The new branch record after version update or None if no update

        """
        version = version or LATEST_VER
        version_updates = self.data_updates(root_id=root_id, version=version)
        # If no new data sources, then exit, nothing to do
        if len(version_updates.data_updates) == 0:
            return None

        use_predictors = []
        if use_existing:
            use_predictors = version_updates.predictors

        branch_instructions = NextBranchVersionRequest(data_updates=version_updates.data_updates,
                                                       use_predictors=use_predictors)
        branch = self.next_version(root_id=root_id,
                                   branch_instructions=branch_instructions,
                                   retrain_models=retrain_models)
        return branch

    def data_updates(self,
                     *,
                     root_id: Union[UUID, str],
                     version: Optional[Union[int, str]] = LATEST_VER) -> BranchDataUpdate:
        """
        Get data updates for a branch.

        Parameters
        ----------
        root_id: Union[UUID, str]
            Unique ID of the branch root

        version: Union[int, str], optional
            The version of the branch. If provided, must either be a positive integer, or "latest".
            Defaults to "latest".

        Returns
        -------
        BranchDataUpdate
            A list of data updates and compatible predictors

        """
        version = version or LATEST_VER
        # The backend API at present expects a branch version ID, so we must look it up.
        uid = self.get(root_id=root_id, version=version).uid

        path = self._get_path(uid=uid, action="data-version-updates-predictor")
        data = self.session.get_resource(path, version=self._api_version)
        return BranchDataUpdate.build(data)

    def next_version(self,
                     root_id: Union[UUID, str],
                     *,
                     branch_instructions: NextBranchVersionRequest,
                     retrain_models: bool = True):
        """
        Move a branch to the next version.

        Parameters
        ----------
        root_id: Union[UUID, str]
            Unique identifier of the branch root to advance to next version

        branch_instructions: NextBranchVersionRequest
            Instructions for how the next version of a branch should handle its predictors
            when the workflows are cloned.  data_updates contains the list of data source
            versions to upgrade (current->latest), and use_predictors will either have a
            <predictor_id>:latest to indicate the workflow should use a new version of
            the predictor.  Or <predictor_id>:<version #> to indicate that the workflow
            should use an existing predictor version.

        retrain_models: bool
            If true, when new versions of models are created, they are automatically
            scheduled for training

        Returns
        -------
        Branch
            The new branch record after version update

        """
        path = self._get_path(action="next-version-predictor")
        data = self.session.post_resource(path, branch_instructions.dump(),
                                          version=self._api_version,
                                          params={
                                              'root': str(root_id),
                                              'retrain_models': retrain_models})
        return self.build(data)

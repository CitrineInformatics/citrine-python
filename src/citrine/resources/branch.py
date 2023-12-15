import functools
import warnings
from typing import Iterator, Optional, Union
from uuid import UUID

from deprecation import deprecated

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import migrate_deprecated_argument
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
        branch_erds_iter = erds.list(root_id=self.uid, version=LATEST_VER)
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

    @deprecated(deprecated_in="2.42.0", removed_in="3.0.0", details="Use .get() instead.")
    def get_by_root_id(self,
                       *,
                       branch_root_id: Union[UUID, str],
                       version: Optional[Union[int, str]] = LATEST_VER) -> Branch:
        """
        Given a branch root ID and (optionally) the version, retrieve the specific branch version.

        Parameters
        ---------
        branch_root_id: Union[UUID, str]
            Unique identifier of the branch root

        version: Union[int, str], optional
            The version of the branch to retrieve. If provided, must either be a positive integer,
            or "latest". Defaults to "latest".

        Returns
        -------
        Branch
            The requested version of the branch.

        """
        return self.get(root_id=branch_root_id, version=version)

    def get(self,
            uid: Optional[Union[UUID, str]] = None,
            *,
            root_id: Optional[Union[UUID, str]] = None,
            version: Optional[Union[int, str]] = LATEST_VER) -> Branch:
        """
        Retrieve a branch using either the version ID, or the root ID and version number.

        Providing both the version ID and the root ID, or neither, will result in an error.

        Providing the root ID and no version number will retrieve the latest version.

        Using the version ID with this method is deprecated in favor of .get_by_version_id().

        Parameters
        ---------
        uid: Union[UUID, str], optional
            [deprecated] Unqiue ID of the branch version.

        root_id: Union[UUID, str], optional
            Unique identifier of the branch root

        version: Union[int, str], optional
            The version of the branch to retrieve. If provided, must either be a positive integer,
            or "latest". Defaults to "latest".

        Returns
        -------
        Branch
            The requested version of the branch.

        """
        if uid:
            warnings.warn("Retrieving a branch by its version ID using .get() is deprecated. "
                          "Please use .get_by_version_id().",
                          DeprecationWarning)

            if root_id:
                raise ValueError("Please provide exactly one: the version ID or root ID.")
            return self.get_by_version_id(version_id=uid)
        elif root_id:
            params = {"root": str(root_id), "version": version or LATEST_VER}
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

        else:
            raise ValueError("Please provide exactly one: the version ID or root ID.")

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
        List all branches using pagination.

        Yields all branches, regardless of archive status, paginating over all available pages.

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
        warnings.warn("Beginning in the 3.0 release, this method will only list unarchived "
                      "branches. To list all branches, use .list_all().",
                      DeprecationWarning)
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
                uid: Optional[Union[UUID, str]] = None,
                *,
                root_id: Optional[Union[UUID, str]] = None,
                version: Optional[int] = None):
        """
        Archive a branch.

        Parameters
        ----------
        uid: Union[UUID, str], optional
            [deprecated] Unique identifier of the branch

        root_id: Union[UUID, str], optional
            Unique ID of the branch root

        version: int, optional
            The version of the branch. If provided, must be a positive integer.

        """
        if uid:
            warnings.warn("Archiving a branch by its version ID is deprecated. "
                          "Please use its root ID and version number.",
                          DeprecationWarning)
        elif root_id:
            if not version or isinstance(version, str):
                raise ValueError("Must provide a version number to archive a branch.")
            # The backend API at present expects a branch version ID, so we must look it up.
            uid = self.get(root_id=root_id, version=version).uid
        else:
            raise ValueError("Please provide exactly one: the version ID or root ID.")

        url = self._get_path(uid, action="archive")
        data = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(data)

    def restore(self,
                uid: Optional[Union[UUID, str]] = None,
                *,
                root_id: Optional[Union[UUID, str]] = None,
                version: Optional[int] = None):
        """
        Restore an archived branch.

        Parameters
        ----------
        uid: Union[UUID, str], optional
            [deprecated] Unique identifier of the branch

        root_id: Union[UUID, str], optional
            Unique ID of the branch root

        version: int, optional
            The version of the branch. If provided, must be a positive integer.

        """
        if uid:
            warnings.warn("Restoring a branch by its version ID is deprecated. "
                          "Please use its root ID and version number.",
                          DeprecationWarning)
        elif root_id:
            if not version or isinstance(version, str):
                raise ValueError("Must provide a version number to restore a branch.")
            # The backend API at present expects a branch version ID, so we must look it up.
            uid = self.get(root_id=root_id, version=version).uid
        else:
            raise ValueError("Please provide exactly one: the version ID or root ID.")

        url = self._get_path(uid, action="restore")
        data = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(data)

    def update_data(self,
                    branch: Optional[Union[UUID, str, Branch]] = None,
                    *,
                    root_id: Optional[Union[UUID, str]] = None,
                    version: Optional[int] = None,
                    use_existing: bool = True,
                    retrain_models: bool = False) -> Optional[Branch]:
        """
        Automatically advance the branch to the next version.

        If there are no newer versions of data sources used by this branch this method returns
        without doing anything

        Parameters
        ----------
        branch: Union[UUID, str, Branch], optional
            [deprecated] Branch Identifier or Branch object

        root_id: Union[UUID, str], optional
            Unique ID of the branch root

        version: int, optional
            The version of the branch. If provided, must be a positive integer.

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
        if branch:
            if root_id:
                raise ValueError("Please provide exactly one: the version ID or root ID.")

            if isinstance(branch, Branch):
                warnings.warn("Updating a branch's data by its object is deprecated. "
                              "Please use its root ID and version number.",
                              DeprecationWarning)
            else:
                warnings.warn("Updating a branch's data by its version ID is deprecated. "
                              "Please use its root ID and version number.",
                              DeprecationWarning)
                branch = self.get_by_version_id(version_id=branch)
            root_id = branch.root_id
            version = branch.version
        elif not root_id:
            raise ValueError("Please provide exactly one: the version ID or root ID.")

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
                     uid: Optional[Union[UUID, str]] = None,
                     *,
                     root_id: Optional[Union[UUID, str]] = None,
                     version: Optional[int] = None) -> BranchDataUpdate:
        """
        Get data updates for a branch.

        Parameters
        ----------
        uid: Union[UUID, str], optional
            [deprecated] Unqiue ID of the branch version.

        root_id: Union[UUID, str], optional
            Unique ID of the branch root

        version: int, optional
            The version of the branch. If provided, must be a positive integer.

        Returns
        -------
        BranchDataUpdate
            A list of data updates and compatible predictors

        """
        if uid:
            warnings.warn("Retrieving data updates for a branch by its version ID is deprecated. "
                          "Please use its root ID and version number.",
                          DeprecationWarning)
            if root_id:
                raise ValueError("Please provide exactly one: the version ID or root ID.")
        elif root_id:
            if version is None or isinstance(version, str):
                raise ValueError("Must provide a version number to retrieve data updates.")
            # The backend API at present expects a branch version ID, so we must look it up.
            uid = self.get(root_id=root_id, version=version).uid
        else:
            raise ValueError("Please provide exactly one: the version ID or root ID.")

        path = self._get_path(uid=uid, action="data-version-updates-predictor")
        data = self.session.get_resource(path, version=self._api_version)
        return BranchDataUpdate.build(data)

    def next_version(self,
                     branch_root_id: Optional[Union[UUID, str]] = None,
                     root_id: Optional[Union[UUID, str]] = None,
                     *,
                     branch_instructions: NextBranchVersionRequest,
                     retrain_models: bool = True):
        """
        Move a branch to the next version.

        Parameters
        ----------
        branch_root_id: Union[UUID, str], optional
            [deprecated] Unique identifier of the branch root to advance to next version.
            Deprecated in favor of root_id.

        root_id: Union[UUID, str], optional
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
        root_id = migrate_deprecated_argument(root_id, "root_id", branch_root_id, "branch_root_id")

        path = self._get_path(action="next-version-predictor")
        data = self.session.post_resource(path, branch_instructions.dump(),
                                          version=self._api_version,
                                          params={
                                              'root': str(root_id),
                                              'retrain_models': retrain_models})
        return self.build(data)

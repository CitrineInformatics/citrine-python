from copy import deepcopy
from typing import Callable, Union, Iterable, Optional, Tuple
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.exceptions import NotFound
from citrine.informatics.workflows import DesignWorkflow
from citrine.resources.response import Response
from functools import partial


class DesignWorkflowCollection(Collection[DesignWorkflow]):
    """A collection of DesignWorkflows."""

    _path_template = '/projects/{project_id}/design-workflows'
    _individual_key = None
    _collection_key = 'response'
    _resource = DesignWorkflow
    _api_version = "v2"

    def __init__(self,
                 project_id: UUID,
                 session: Session,
                 *,
                 branch_root_id: Optional[UUID] = None,
                 branch_version: Optional[int] = None):
        self.project_id: UUID = project_id
        self.session: Session = session

        self.branch_root_id = branch_root_id
        self.branch_version = branch_version

    def _resolve_branch_root_and_version(self, workflow):
        from citrine.resources.branch import BranchCollection

        workflow_copy = deepcopy(workflow)
        bc = BranchCollection(self.project_id, self.session)
        branch = bc.get_by_version_id(version_id=workflow_copy._branch_id)
        workflow_copy._branch_root_id = branch.root_id
        workflow_copy._branch_version = branch.version
        return workflow_copy

    def _resolve_branch_id(self, root_id, version):
        from citrine.resources.branch import BranchCollection

        if root_id and version:
            bc = BranchCollection(self.project_id, self.session)
            branch = bc.get(root_id=root_id, version=version)
            return branch.uid
        return None

    def register(self, model: DesignWorkflow) -> DesignWorkflow:
        """
        Upload a new design workflow.

        The model's branch root ID and branch version are ignored in favor of this collection's.
        If this collection has a null branch root ID or branch version, an exception is raised
        directing the caller to use one.

        Parameters
        ----------
        model: DesignWorkflow
            The design workflow to be uploaded.

        Return
        -------
        DesignWorkflow
            The newly created design workflow.

        """
        if self.branch_root_id is None or self.branch_version is None:
            # There are a number of contexts in which hitting design workflow endpoints without
            # a branch ID is valid, so only this particular usage is disallowed.
            msg = ('A design workflow must be created with a branch. Please use '
                   'branch.design_workflows.register() instead of '
                   'project.design_workflows.register().')
            raise RuntimeError(msg)
        else:
            # branch_id is in the body of design workflow endpoints, so it must be serialized.
            # This means the collection branch_id might not match the workflow branch_id. The
            # collection should win out, since the user is explicitly referencing the branch
            # represented by this collection.
            # To avoid modifying the parameter, and to ensure the only change is the branch_id, we
            # deepcopy, modify, then register it.
            model_copy = deepcopy(model)
            model_copy._branch_id = self._resolve_branch_id(self.branch_root_id,
                                                            self.branch_version)
            return super().register(model_copy)

    def build(self, data: dict) -> DesignWorkflow:
        """
        Build an individual design workflow from a dictionary.

        Parameters
        ----------
        data: dict
            A dictionary representing the design workflow.

        Return
        -------
        DesignWorkflow
            The design workflow created from data.

        """
        workflow = DesignWorkflow.build(data)
        workflow = self._resolve_branch_root_and_version(workflow)
        workflow._session = self.session
        workflow.project_id = self.project_id
        return workflow

    def update(self, model: DesignWorkflow) -> DesignWorkflow:
        """Update a design workflow.

        Identifies the workflow by its uid. It must have a branch_root_id and branch_version, and
        if this collection also has a branch_root_id and branch_version, they must match. Prefer
        updating a workflow through Project.design_workflows.update.

        Parameters
        ----------
        model: DesignWorkflow
            The design workflow values that are desired, identified by the uid.

        Return
        -------
        DesignWorkflow
            The design workflow resulting from the update.

        """
        if self.branch_root_id is not None or self.branch_version is not None:
            if self.branch_root_id != model.branch_root_id or \
                    self.branch_version != model.branch_version:
                raise ValueError('To move a design workflow to another branch, please use '
                                 'Project.design_workflows.update')

        if model.branch_root_id is None or model.branch_version is None:
            raise ValueError('Cannot update a design workflow unless its branch_root_id and '
                             'branch_version are set.')

        try:
            model._branch_id = self._resolve_branch_id(model.branch_root_id,
                                                       model.branch_version)
        except NotFound:
            raise ValueError('Cannot update a design workflow unless its branch_root_id and '
                             'branch_version exists.')

        # If executions have already been done, warn about future behavior change
        executions = model.design_executions.list()
        if next(executions, None) is not None:
            raise RuntimeError("Cannot update a design workflow after candidate generation, "
                               "please register a new design workflow instead")

        return super().update(model)

    def archive(self, uid: Union[UUID, str]):
        """Archive a design workflow.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the workflow to archive

        """
        url = self._get_path(uid=uid, action="archive")
        self.session.put_resource(url, {}, version=self._api_version)

    def restore(self, uid: Union[UUID, str]):
        """Restore an archived design workflow.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the workflow to restore

        """
        url = self._get_path(uid=uid, action="restore")
        self.session.put_resource(url, {}, version=self._api_version)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Design Workflows cannot be deleted; they can be archived instead."""
        raise NotImplementedError(
            "Design Workflows cannot be deleted; they can be archived instead.")

    def list_archived(self, *, per_page: int = 500) -> Iterable[DesignWorkflow]:
        """List archived Design Workflows."""
        fetcher = partial(self._fetch_page, additional_params={"filter": "archived eq 'true'"})
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def _fetch_page(self,
                    path: Optional[str] = None,
                    fetch_func: Optional[Callable[..., dict]] = None,
                    page: Optional[int] = None,
                    per_page: Optional[int] = None,
                    json_body: Optional[dict] = None,
                    additional_params: Optional[dict] = None,
                    ) -> Tuple[Iterable[dict], str]:
        params = additional_params or {}
        params["branch"] = self._resolve_branch_id(self.branch_root_id, self.branch_version)
        return super()._fetch_page(path=path,
                                   fetch_func=fetch_func,
                                   page=page,
                                   per_page=per_page,
                                   json_body=json_body,
                                   additional_params=params)

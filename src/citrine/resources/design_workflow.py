from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine._utils.functions import migrate_deprecated_argument
from citrine.informatics.workflows import DesignWorkflow
from citrine.resources.response import Response
from typing import Optional, Union, Iterable


class DesignWorkflowCollection(Collection[DesignWorkflow]):
    """A collection of DesignWorkflows."""

    _path_template = '/projects/{project_id}/design-workflows'
    _individual_key = None
    _collection_key = 'response'
    _resource = DesignWorkflow

    def __init__(self, project_id: UUID, session: Session):
        self.project_id: UUID = project_id
        self.session: Session = session

    def build(self, data: dict) -> DesignWorkflow:
        """Build an individual DesignExecution."""
        workflow = DesignWorkflow.build(data)
        workflow._session = self.session
        workflow.project_id = self.project_id
        return workflow

    def archive(self, uid: Union[UUID, str] = None, workflow_id: Union[UUID, str] = None):
        """Archive a design workflow.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the workflow to archive
        workflow_id: Union[UUID, str]
            [DEPRECATED] please use uid instead

        """
        uid = migrate_deprecated_argument(uid, "uid", workflow_id, "workflow_id")
        url = self._path_template.format(project_id=self.project_id) \
            + "/{}/archive".format(uid)
        self.session.put_resource(url, {})

    def restore(self, uid: Union[UUID, str] = None, workflow_id: [UUID, str] = None):
        """Restore an archived design workflow.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the workflow to restore
        workflow_id: Union[UUID, str]
            [DEPRECATED] please use uid instead

        """
        uid = migrate_deprecated_argument(uid, "uid", workflow_id, "workflow_id")
        url = self._path_template.format(project_id=self.project_id) \
            + "/{}/restore".format(uid)
        self.session.put_resource(url, {})

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Design Workflows cannot be deleted; they can be archived instead."""
        raise NotImplementedError(
            "Design Workflows cannot be deleted; they can be archived instead.")

    def list_archived(self,
                      *,
                      page: Optional[int] = None,
                      per_page: int = 500) -> Iterable[DesignWorkflow]:
        """List archived Design Workflows"""
        return self.session.get_resource(path=self._get_path(),
                                         params={'page': page, 'per_page': per_page, 'filter': "archived eq 'true'"}
                                         )

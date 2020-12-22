from typing import Union
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.workflows import DesignWorkflow
from citrine.resources.response import Response


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
        workflow.session = self.session
        workflow.project_id = self.project_id
        return workflow

    def archive(self, workflow_id: UUID):
        """Archive a predictor evaluation workflow.

        Parameters
        ----------
        workflow_id: UUID
            Unique identifier of the workflow to archive

        """
        url = self._path_template.format(project_id=self.project_id) \
            + "/{}/archive".format(workflow_id)
        self.session.put_resource(url, {})

    def restore(self, workflow_id: UUID):
        """Restore a predictor evaluation workflow.

        Parameters
        ----------
        workflow_id: UUID
            Unique identifier of the workflow to restore

        """
        url = self._path_template.format(project_id=self.project_id) \
            + "/{}/restore".format(workflow_id)
        self.session.put_resource(url, {})

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Predictor Evaluation Workflows cannot be deleted; they can be archived instead."""
        raise NotImplementedError(
            "Design Workflows cannot be deleted; they can be archived instead.")

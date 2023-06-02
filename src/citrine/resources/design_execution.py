"""Resources that represent both individual and collections of design workflow executions."""
from typing import Optional, Union, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._utils.functions import MigratedClassMeta
from citrine._session import Session
from citrine.informatics import executions
from citrine.informatics.scores import Score
from citrine.resources.response import Response


class DesignExecution(executions.DesignExecution,
                      deprecated_in="2.22.1",
                      removed_in="3.0.0",
                      metaclass=MigratedClassMeta):
    """The execution of a DesignWorkflow.

    Possible statuses are INPROGRESS, SUCCEEDED, and FAILED.
    Design executions also have a ``status_description`` field with more information.

    DesignExecution should be imported from citrine.informatics.executions.

    """


class DesignExecutionCollection(Collection["DesignExecution"]):
    """A collection of DesignExecutions."""

    _path_template = '/projects/{project_id}/design-workflows/{workflow_id}/executions'  # noqa
    _individual_key = None
    _collection_key = 'response'
    _resource = executions.DesignExecution

    def __init__(self,
                 project_id: UUID,
                 session: Session,
                 workflow_id: Optional[UUID] = None):
        self.project_id: UUID = project_id
        self.session: Session = session
        self.workflow_id: UUID = workflow_id

    def build(self, data: dict) -> executions.DesignExecution:
        """Build an individual DesignWorkflowExecution."""
        execution = executions.DesignExecution.build(data)
        execution._session = self.session
        execution.project_id = self.project_id
        return execution

    def trigger(self, execution_input: Score, *, max_candidates: Optional[int] = None):
        """Trigger a Design Workflow execution given a score and a maximum number of candidates."""
        path = self._get_path()
        json = {'score': execution_input.dump(), "max_candidates": max_candidates}
        data = self.session.post_resource(path, json)
        return self.build(data)

    def register(self, model: executions.DesignExecution) -> executions.DesignExecution:
        """Cannot register an execution."""
        raise NotImplementedError("Cannot register a DesignExecution.")

    def update(self, model: executions.DesignExecution) -> executions.DesignExecution:
        """Cannot update an execution."""
        raise NotImplementedError("Cannot update a DesignExecution.")

    def archive(self, uid: Union[UUID, str]):
        """Archive a Design Workflow execution.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the execution to archive

        """
        raise NotImplementedError(
            "Design Executions cannot be archived")

    def restore(self, uid: UUID):
        """Restore an archived Design Workflow execution.

        Parameters
        ----------
        uid: UUID
            Unique identifier of the execution to restore

        """
        raise NotImplementedError(
            "Design Executions cannot be restored")

    def list(self, *, per_page: int = 100) -> Iterator[executions.DesignExecution]:
        """
        Paginate over the elements of the collection.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        Returns
        -------
        Iterator[ResourceType]
            Resources in this collection.

        """
        return self._paginator.paginate(page_fetcher=self._fetch_page,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Design Workflow Executions cannot be deleted or archived."""
        raise NotImplementedError(
            "Design Executions cannot be deleted")

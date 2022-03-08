"""Resources that represent both individual and collections of design workflow executions."""
import sys
from typing import Optional, Union, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._utils.functions import shadow_classes_in_module
from citrine._session import Session
import citrine.informatics.executions.design_execution
from citrine.informatics.executions import DesignExecution
from citrine.informatics.scores import Score
from citrine.resources.response import Response


shadow_classes_in_module(citrine.informatics.executions.design_execution, sys.modules[__name__])


class DesignExecutionCollection(Collection["DesignExecution"]):
    """A collection of DesignExecutions."""

    _path_template = '/projects/{project_id}/design-workflows/{workflow_id}/executions'  # noqa
    _individual_key = None
    _collection_key = 'response'
    _resource = DesignExecution

    def __init__(self,
                 project_id: UUID,
                 session: Session,
                 workflow_id: Optional[UUID] = None):
        self.project_id: UUID = project_id
        self.session: Session = session
        self.workflow_id: UUID = workflow_id

    def build(self, data: dict) -> DesignExecution:
        """Build an individual DesignWorkflowExecution."""
        execution = DesignExecution.build(data)
        execution._session = self.session
        execution.project_id = self.project_id
        return execution

    def trigger(self, execution_input: Score):
        """Trigger a Design Workflow execution given a score."""
        path = self._get_path()
        data = self.session.post_resource(path, {'score': execution_input.dump()})
        return self.build(data)

    def register(self, model: DesignExecution) -> DesignExecution:
        """Cannot register an execution."""
        raise NotImplementedError("Cannot register a DesignExecution.")

    def update(self, model: DesignExecution) -> DesignExecution:
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

    def list(self, *,
             page: Optional[int] = None,
             per_page: int = 100,
             ) -> Iterator[DesignExecution]:
        """
        Paginate over the elements of the collection.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is to read all pages and yield
            all results.  This option is deprecated.
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.
        predictor_id: uuid, optional
            list executions that targeted the predictor with this id

        Returns
        -------
        Iterator[ResourceType]
            Resources in this collection.

        """
        return self._paginator.paginate(page_fetcher=self._fetch_page,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
                                        per_page=per_page)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Design Workflow Executions cannot be deleted or archived."""
        raise NotImplementedError(
            "Design Executions cannot be deleted")

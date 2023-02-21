"""Resources that represent both individual and collections of design workflow executions."""
from typing import Union, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.executions.generative_design_execution import GenerativeDesignExecution
from citrine.informatics.generative_design import GenerativeDesignInput
from citrine.resources.response import Response


class GenerativeDesignExecutionCollection(Collection["GenerativeDesignExecution"]):
    """A collection of GenerativeDesignExecutions."""

    _path_template = '/projects/{project_id}/generative-design/executions'
    _individual_key = None
    _collection_key = 'response'
    _resource = GenerativeDesignExecution

    def __init__(self, project_id: UUID, session: Session):
        self.project_id: UUID = project_id
        self.session: Session = session

    def build(self, data: dict) -> GenerativeDesignExecution:
        """Build an individual GenerativeDesignExecution."""
        execution = GenerativeDesignExecution.build(data)
        execution._session = self.session
        execution.project_id = self.project_id
        return execution

    def trigger(
        self, generative_design_execution_input: GenerativeDesignInput
    ) -> GenerativeDesignExecution:
        """Trigger a Generative Design execution."""
        path = self._get_path()
        request_dict = generative_design_execution_input.dump()
        data = self.session.post_resource(path, request_dict)
        return self.build(data)

    def register(self, model: GenerativeDesignExecution) -> GenerativeDesignExecution:
        """Cannot register an execution."""
        raise NotImplementedError("Cannot register a GenerativeDesignExecution.")

    def update(self, model: GenerativeDesignExecution) -> GenerativeDesignExecution:
        """Cannot update an execution."""
        raise NotImplementedError("Cannot update a GenerativeDesignExecution.")

    def list(self, *, per_page: int = 10) -> Iterator[GenerativeDesignExecution]:
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
        """Generative Design Executions cannot be deleted or archived."""
        raise NotImplementedError(
            "Generative Design Executions cannot be deleted"
        )

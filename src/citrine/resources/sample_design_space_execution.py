"""Resources that represent both individual and collections of sample design space executions."""
from typing import Union, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.executions.sample_design_space_execution import SampleDesignSpaceExecution
from citrine.informatics.design_spaces.sample_design_space import SampleDesignSpaceInput
from citrine.resources.response import Response


class SampleDesignSpaceExecutionCollection(Collection["SampleDesignSpaceExecution"]):
    """A collection of SampleDesignSpaceExecutions."""

    _api_version = 'v3'
    _path_template = '/projects/{project_id}/design-spaces/{design_space_id}/sample'
    _individual_key = None
    _collection_key = 'response'
    _resource = SampleDesignSpaceExecution

    def __init__(self, project_id: UUID, design_space_id: UUID, session: Session):
        self.project_id: UUID = project_id
        self.design_space_id: UUID = design_space_id
        self.session: Session = session

    def build(self, data: dict) -> SampleDesignSpaceExecution:
        """Build an individual SampleDesignSpaceExecution."""
        execution = SampleDesignSpaceExecution.build(data)
        execution._session = self.session
        execution.project_id = self.project_id
        execution.design_space_id = self.design_space_id
        return execution

    def trigger(
        self, sample_design_space_input: SampleDesignSpaceInput
    ) -> SampleDesignSpaceExecution:
        """Trigger a sample design space execution."""
        path = self._get_path()
        request_dict = sample_design_space_input.dump()
        data = self.session.post_resource(path, request_dict, version=self._api_version)
        return self.build(data)

    def register(self, model: SampleDesignSpaceExecution) -> SampleDesignSpaceExecution:
        """Cannot register an execution."""
        raise NotImplementedError("Cannot register a SampleDesignSpaceExecution.")

    def update(self, model: SampleDesignSpaceExecution) -> SampleDesignSpaceExecution:
        """Cannot update an execution."""
        raise NotImplementedError("Cannot update a SampleDesignSpaceExecution.")

    def list(self, *,
             per_page: int = 10,
             ) -> Iterator[SampleDesignSpaceExecution]:
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
        """Sample Design Space Executions cannot be deleted or archived."""
        raise NotImplementedError(
            "Sample Design Space Executions cannot be deleted"
        )

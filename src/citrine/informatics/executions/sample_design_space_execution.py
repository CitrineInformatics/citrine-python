from functools import partial
from typing import Optional, Iterable
from uuid import UUID

from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._rest.pageable import Pageable
from citrine._rest.paginator import Paginator
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.informatics.design_candidate import SampleSearchSpaceResultCandidate


class SampleDesignSpaceExecution(
    Resource["SampleDesignSpaceExecution"], Pageable, AsynchronousObject
):
    """The execution of a Sample Design Space task.

    Possible statuses are INPROGRESS, SUCCEEDED, and FAILED.
    Design executions also have a ``status_description`` field with more information.
    """

    _paginator: Paginator = Paginator()
    _collection_key = 'response'
    _in_progress_statuses = ["INPROGRESS"]
    _succeeded_statuses = ["SUCCEEDED"]
    _failed_statuses = ["FAILED"]
    _session: Optional[Session] = None
    project_id: Optional[UUID] = None
    design_space_id: Optional[UUID] = None

    uid: UUID = properties.UUID('id', serializable=False)
    """:UUID: Unique identifier of the execution"""
    status = properties.Optional(properties.String(), 'status', serializable=False)
    """:Optional[str]: short description of the execution's status"""
    status_description = properties.Optional(
        properties.String(), 'status_description', serializable=False)
    """:Optional[str]: more detailed description of the execution's status"""
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )

    """:Optional[List[str]]: human-readable explanations of the status"""
    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    """:Optional[UUID]: id of the user who created the resource"""
    updated_by = properties.Optional(properties.UUID, 'updated_by', serializable=False)
    """:Optional[UUID]: id of the user who most recently updated the resource,
    if it has been updated"""
    create_time = properties.Optional(properties.Datetime, 'create_time', serializable=False)
    """:Optional[datetime]: date and time at which the resource was created"""
    update_time = properties.Optional(properties.Datetime, 'update_time', serializable=False)
    """:Optional[datetime]: date and time at which the resource was most recently updated,
    if it has been updated"""

    def __init__(self):
        """The SampleDesignSpace executions are not directly instantiated by the user."""
        pass  # pragma: no cover

    def __str__(self):
        return '<SampleDesignSpaceExecution {!r}>'.format(str(self.uid))

    def _path(self):
        return format_escaped_url(
            '/projects/{project_id}/design-spaces/{design_space_id}/sample/',
            project_id=self.project_id,
            design_space_id=self.design_space_id,
        )

    @classmethod
    def _build_results(
        cls, subset_collection: Iterable[dict]
    ) -> Iterable[SampleSearchSpaceResultCandidate]:
        for sample_result in subset_collection:
            yield SampleSearchSpaceResultCandidate.build(sample_result)

    def results(
        self,
        *,
        page: Optional[int] = None,
        per_page: int = 100,
    ) -> Iterable[SampleSearchSpaceResultCandidate]:
        """Fetch the Sample Design Space Results for the particular execution, paginated."""
        path = self._path() + f'{self.uid}/results'
        fetcher = partial(self._fetch_page, path=path, fetch_func=self._session.get_resource)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_results,
                                        per_page=per_page)

    def result(
        self,
        *,
        result_id: UUID,
    ) -> SampleSearchSpaceResultCandidate:
        """Fetch a Sample Design Space Result for the particular UID."""
        path = self._path() + f'{self.uid}/results/{result_id}'
        data = self._session.get_resource(path, version=self._api_version)
        result = SampleSearchSpaceResultCandidate.build(data)
        return result

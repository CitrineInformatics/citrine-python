from functools import partial
from typing import Iterable, List, Optional
from uuid import UUID

from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._rest.pageable import Pageable
from citrine._rest.paginator import Paginator
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.informatics.generative_design import GenerativeDesignResult
from citrine.resources.status_detail import StatusDetail

from deprecation import deprecated


class GenerativeDesignExecution(
    Resource["GenerativeDesignExecution"], Pageable, AsynchronousObject
):
    """The execution of a Generative Design task.

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

    uid: UUID = properties.UUID('id', serializable=False)
    """:UUID: Unique identifier of the execution"""
    status = properties.Optional(properties.String(), 'status', serializable=False)
    """:Optional[str]: short description of the execution's status"""
    status_description = properties.Optional(
        properties.String(), 'status_description', serializable=False)
    """:Optional[str]: more detailed description of the execution's status"""
    status_detail = properties.List(properties.Object(StatusDetail), 'status_detail', default=[],
                                    serializable=False)
    """:List[StatusDetail]: a list of structured status info, containing the message and level"""

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

    @property
    @deprecated(deprecated_in="2.2.0", removed_in="3.0.0", details="Use status_detail instead.")
    def status_info(self) -> List[str]:
        """:List[str]: human-readable explanations of the status."""
        return [detail.msg for detail in self.status_detail]

    def __init__(self):
        """The GenerativeDesign executions are not directly instantiated by the user."""
        pass  # pragma: no cover

    def __str__(self):
        return '<GenerativeDesignExecution {!r}>'.format(str(self.uid))

    def _path(self):
        return format_escaped_url(
            '/projects/{project_id}/generative-design/executions/',
            project_id=self.project_id,
        )

    @classmethod
    def _build_results(
        cls, subset_collection: Iterable[dict]
    ) -> Iterable[GenerativeDesignResult]:
        for generation_result in subset_collection:
            yield GenerativeDesignResult.build(generation_result)

    def results(self, *, per_page: int = 100) -> Iterable[GenerativeDesignResult]:
        """Fetch the Generative Design Results for the particular execution, paginated."""
        path = self._path() + f'{self.uid}/results'
        fetcher = partial(self._fetch_page, path=path, fetch_func=self._session.get_resource)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_results,
                                        per_page=per_page)

    def result(
        self,
        *,
        result_id: UUID,
    ) -> GenerativeDesignResult:
        """Fetch a Generative Design Result for the particular UID."""
        path = self._path() + f'{self.uid}/results/{result_id}'
        data = self._session.get_resource(path, version=self._api_version)
        result = GenerativeDesignResult.build(data)
        return result

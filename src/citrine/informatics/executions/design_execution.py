from deprecation import deprecated
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
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.design_candidate import DesignCandidate
from citrine.informatics.predict_request import PredictRequest
from citrine.informatics.scores import Score


class DesignExecution(Resource['DesignExecution'], Pageable, AsynchronousObject):
    """The execution of a DesignWorkflow.

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
    """:Optional[UUID]: Unique ID of the project that contains this workflow execution."""

    uid: UUID = properties.UUID('id', serializable=False)
    """:UUID: Unique identifier of the workflow execution"""
    workflow_id = properties.UUID('workflow_id', serializable=False)
    """:UUID: Unique identifier of the workflow that was executed"""
    version_number = properties.Integer("version_number", serializable=False)
    """:int: Integer identifier that increases each time the workflow is executed. The first
    execution has version_number = 1."""

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

    score = properties.Object(Score, 'score')
    """:Score: score by which this execution was evaluated"""
    descriptors = properties.List(properties.Object(Descriptor), 'descriptors')
    """:List[Descriptor]: all of the descriptors in the candidates generated by this execution"""

    def __init__(self):
        """Design executions are not directly instantiated by the user."""
        pass  # pragma: no cover

    def __str__(self):
        return '<DesignExecution {!r}>'.format(str(self.uid))

    def _path(self):
        return format_escaped_url(
            '/projects/{project_id}/design-workflows/{workflow_id}/executions/{execution_id}',
            project_id=self.project_id,
            workflow_id=self.workflow_id,
            execution_id=self.uid
        )

    @classmethod
    def _build_candidates(cls, subset_collection: Iterable[dict]) -> Iterable[DesignCandidate]:
        for candidate in subset_collection:
            yield DesignCandidate.build(candidate)

    def candidates(self, *,
                   page: Optional[int] = None,
                   per_page: int = 100,
                   ) -> Iterable[DesignCandidate]:
        """Fetch the Design Candidates for the particular execution, paginated."""
        path = self._path() + '/candidates'

        fetcher = partial(self._fetch_page, path=path, fetch_func=self._session.get_resource)

        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_candidates,
                                        page=page,
                                        per_page=per_page)

    def predict(self,
                predict_request: PredictRequest) -> DesignCandidate:
        """Invoke a prediction on a design candidate"""

        path = self._path() + '/predict'

        res = self._session.post_resource(path, predict_request.dump(), version=self._api_version)
        return DesignCandidate.build(res)

    @property
    @deprecated(deprecated_in="1.25.0", removed_in="2.0.0")
    def experimental(self) -> bool:
        """[DEPRECATED] whether the execution is experimental (newer, less well-tested)."""  # noqa - insisting this docstring is a signature
        return False

    @property
    @deprecated(deprecated_in="1.25.0", removed_in="2.0.0")
    def experimental_reasons(self) -> List[str]:
        """[DEPRECATED] human-readable reasons why the execution is experimental."""
        return []

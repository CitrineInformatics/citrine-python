import functools
from typing import Iterator, Optional, Union
from uuid import UUID

from citrine.informatics.workflows.analysis_workflow import AnalysisWorkflow, \
    AnalysisWorkflowUpdatePayload
from citrine._rest.collection import Collection
from citrine._session import Session


class AnalysisWorkflowCollection(Collection[AnalysisWorkflow]):
    """Represents the collection of all analysis workflows for a team.

    Parameters
    ----------
    team_id: UUID
        the UUID of the team

    """

    _api_version = 'v1'
    _path_template = '/teams/{team_id}/analysis-workflows'
    _individual_key = None
    _resource = AnalysisWorkflow
    _collection_key = 'response'

    def __init__(self, session: Session, *, team_id: UUID):
        self.session = session
        self.team_id = team_id

    def build(self, data: dict) -> AnalysisWorkflow:
        """
        Build an individual analysis workflow from a dictionary.

        Parameters
        ----------
        data: dict
            A dictionary representing the analysis workflow.

        Return
        -------
        AnalysisWorkflow
            The analysis workflow created from data.

        """
        workflow = AnalysisWorkflow.build(data)
        workflow.team_id = self.team_id
        return workflow

    def list_all(self, *, per_page: int = 20) -> Iterator[AnalysisWorkflow]:
        """List all analysis workflows."""
        return self._list_with_params(per_page=per_page, include_archived=True)

    def list_archived(self, *, per_page: int = 20) -> Iterator[AnalysisWorkflow]:
        """List archived analysis workflows."""
        return self._list_with_params(per_page=per_page, filter="archived eq 'true'")

    def list(self, *, per_page: int = 20) -> Iterator[AnalysisWorkflow]:
        """List acttive analysis workflows."""
        return self._list_with_params(per_page=per_page, filter="archived eq 'false'")

    def _list_with_params(self, *, per_page: int, **kwargs) -> Iterator[AnalysisWorkflow]:
        page_fetcher = functools.partial(self._fetch_page, additional_params=kwargs)
        return self._paginator.paginate(page_fetcher=page_fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def archive(self, uid: Union[UUID, str]) -> AnalysisWorkflow:
        """Archive an analysis workflow, hiding it from default listings."""
        url = self._get_path(uid=uid, action="archive")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def restore(self, uid: Union[UUID, str]) -> AnalysisWorkflow:
        """Restore an analysis workflow, showing it in default listings."""
        url = self._get_path(uid=uid, action="restore")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def update(self,
               uid: Union[UUID, str],
               *,
               name: Optional[str] = None,
               description: Optional[str] = None) -> AnalysisWorkflow:
        """Update the name and/or description of the analysis workflow."""
        aw_update = AnalysisWorkflowUpdatePayload(uid=uid, name=name, description=description)
        return super().update(aw_update)

    def rebuild(self, uid: Union[UUID, str]) -> AnalysisWorkflow:
        """Rebuild the data source underlying the analysis workflow."""
        url = self._get_path(uid=uid, action=("query", "rerun"))
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def delete(self, uid: Union[UUID, str]):
        """Analysis workflows cannot be deleted at this time."""
        raise NotImplementedError("Deleting Analysis Workflows is not currently supported.")

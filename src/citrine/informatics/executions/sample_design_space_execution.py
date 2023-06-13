from functools import partial
from typing import Optional, Iterable
from uuid import UUID

from citrine.informatics.executions.execution import Execution
from citrine.informatics.design_candidate import SampleSearchSpaceResultCandidate
from citrine._rest.resource import Resource
from citrine._utils.functions import format_escaped_url


class SampleDesignSpaceExecution(Resource['SampleDesignSpaceExecution'], Execution):
    """The execution of a Sample Design Space task.

    Possible statuses are INPROGRESS, SUCCEEDED, and FAILED.
    Additional fields ``status_description`` and ``status_detail`` provide more information.

    """

    design_space_id: Optional[UUID] = None

    def _path(self):
        return format_escaped_url(
            '/projects/{project_id}/design-spaces/{design_space_id}/sample/',
            project_id=self.project_id,
            design_space_id=self.design_space_id,
        )

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        """Run data modification before building."""
        status_dict = data['status']

        # Set major status
        if "major" not in status_dict and status_dict["minor"] in ["EXECUTING", "VALIDATING"]:
            status_dict["major"] = "INPROGRESS"

        # Update data dictionary with minor and detail status
        data["status_description"] = status_dict['minor']
        data["status_detail"] = status_dict['detail']

        # If major status exists, update data dictionary
        if "major" in status_dict:
            data["status"] = status_dict["major"]

        return data

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

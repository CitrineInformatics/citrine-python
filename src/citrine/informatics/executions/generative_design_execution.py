from functools import partial
from typing import Iterable
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._utils.functions import format_escaped_url
from citrine.informatics.generative_design import GenerativeDesignResult
from citrine.informatics.executions.execution import Execution


class GenerativeDesignExecution(Resource["GenerativeDesignExecution"], Execution):
    """The execution of a Generative Design task.

    Possible statuses are INPROGRESS, SUCCEEDED, and FAILED.
    Design executions also have a ``status_description`` field with more information.

    """

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

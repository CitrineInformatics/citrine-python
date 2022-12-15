"""A resource that represents a single module report."""
from typing import Optional, Union
from uuid import UUID

from deprecation import deprecated

from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine._utils.functions import migrate_deprecated_argument
from citrine.informatics.reports import Report


class ReportResource(Resource['ReportResource']):
    """Defines a resource for fetching reports from a module.

    Parameters
    ----------
    project_id: UUID
        the UUID of the project

    """

    _path_template = '/projects/{project_id}/predictors/{predictor_id}/versions/{version}/report'
    _api_version = 'v3'

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session = session

    def get(self,
            module_id: UUID = None,
            *,
            predictor_id: Union[UUID, str] = None,
            predictor_version: Optional[Union[int, str]] = None) -> Report:
        """Gets a single report keyed on the predictor ID and (optionally) version."""
        predictor_id = migrate_deprecated_argument(predictor_id, "predictor_id",
                                                   module_id, "module_id")
        version = predictor_version or "most_recent"

        url_path = format_escaped_url(self._path_template,
                                      project_id=self.project_id,
                                      predictor_id=str(predictor_id),
                                      version=version)
        data = self.session.get_resource(url_path, version=self._api_version)

        report = Report.build(data)
        report.session = self.session
        return report

    @deprecated(deprecated_in="1.49.0", removed_in="2.0.0",
                details="Please use ReportResource.get() instead.")
    def get_version(self, predictor_id: Union[UUID, str], *, predictor_version: Union[int, str]) \
            -> Report:
        """Gets a single report keyed on the predictor ID and version."""
        return self.get(predictor_id=predictor_id, predictor_version=predictor_version)

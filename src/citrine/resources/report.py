"""A resource that represents a single module report."""
from typing import Optional, Union
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
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
            *,
            predictor_id: Union[UUID, str],
            predictor_version: Optional[Union[int, str]] = None) -> Report:
        """Gets a single report keyed on the predictor ID and (optionally) version."""
        version = predictor_version or "most_recent"

        url_path = format_escaped_url(self._path_template,
                                      project_id=self.project_id,
                                      predictor_id=str(predictor_id),
                                      version=version)
        data = self.session.get_resource(url_path, version=self._api_version)

        report = Report.build(data)
        report.session = self.session
        return report

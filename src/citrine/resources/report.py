"""A resource that represents a single module report."""
from typing import Union
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

    _path_template = '/projects/{project_id}/modules/{module_id}/report'

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session = session

    def get(self, module_id: UUID) -> Report:
        """Gets a single report keyed on the module_id."""
        url_path = format_escaped_url(self._path_template,
                                      project_id=self.project_id,
                                      module_id=module_id)
        data = self.session.get_resource(url_path)
        report = Report.build(data)
        report.session = self.session
        return report

    def get_version(self, predictor_id: Union[UUID, str], *, predictor_version: Union[int, str]) \
            -> Report:
        """Gets a single report keyed on the module_id."""
        path_template = ('/projects/{project_id}/predictors/{predictor_id}/versions/{version}'
                         '/report')
        url_path = format_escaped_url(path_template,
                                      project_id=self.project_id,
                                      predictor_id=str(predictor_id),
                                      version=predictor_version)
        data = self.session.get_resource(url_path, version="v3")
        report = Report.build(data)
        report.session = self.session
        return report

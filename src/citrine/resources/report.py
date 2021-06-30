"""A resource that represents a single module report."""
from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.informatics.reports import Report

from uuid import UUID


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

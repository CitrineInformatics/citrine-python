"""A resource that represents a single module report."""
from citrine._rest.resource import Resource
from citrine._session import Session
from citrine.informatics.reports import Report

from uuid import UUID


class ReportResource(Resource['ReportResource']):

    _path_template = '/projects/{project_id}/modules/{module_id}/report'

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session = session

    def get(self, module_id: UUID) -> Report:
        url_path = self._path_template.format(project_id=self.project_id, module_id=module_id)
        data = self.session.get_resource(url_path)
        report = Report.build(data)
        report.session = self.session
        return report

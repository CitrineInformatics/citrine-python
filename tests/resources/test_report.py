"""Tests getting a report"""
import uuid

from citrine.resources.report import ReportResource

import mock


def test_get_report():
    """Validates the proper url is called"""
    session = mock.Mock()
    session.get_resource.return_value = dict(status='PENDING', report=dict(), uid=str(str(uuid.uuid4())))
    project_id = uuid.uuid4()
    module_id = uuid.uuid4()
    rr = ReportResource(project_id, session)
    report = rr.get(module_id)
    assert report.status == 'PENDING'
    assert session.get_resource.call_count == 1
    assert session.get_resource.call_args == mock.call(f'/projects/{project_id}/modules/{module_id}/report')
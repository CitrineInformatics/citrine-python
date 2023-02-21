"""Tests getting a report"""
import random
import uuid

import pytest

from citrine.resources.report import ReportResource

from tests.utils.session import FakeCall, FakeSession


def test_get_report():
    project_id = uuid.uuid4()
    predictor_id = uuid.uuid4()
    report_path = f'/projects/{project_id}/predictors/{predictor_id}/versions/most_recent/report'

    session = FakeSession()
    session.set_response(dict(status='PENDING',
                              report=dict(descriptors=[], models=[]),
                              uid=str(str(uuid.uuid4()))))

    report = ReportResource(project_id, session).get(predictor_id=predictor_id)

    assert report.status == 'PENDING'
    assert session.calls == [FakeCall(method="GET", path=report_path)]


def test_get_report_with_version():
    project_id = uuid.uuid4()
    predictor_id = uuid.uuid4()
    predictor_version = random.randint(1, 10)
    report_path = f'/projects/{project_id}/predictors/{predictor_id}/versions/{predictor_version}/report'

    session = FakeSession()
    session.set_response(dict(status='PENDING',
                              report=dict(descriptors=[], models=[]),
                              uid=str(str(uuid.uuid4()))))

    report = ReportResource(project_id, session).get(predictor_id=predictor_id, predictor_version=predictor_version)

    assert report.status == 'PENDING'
    assert session.calls == [FakeCall(method="GET", path=report_path)]

"""Tests for citrine.informatics.reports serialization."""
import pytest
import uuid

from citrine.informatics.reports import Report, PredictorReport


@pytest.fixture
def valid_report_data():
    """Produce valid data for making a report."""
    return dict(
        id=str(uuid.uuid4()),
        status='OK',
        report=dict(key1='value1', key2='value2'),
    )


def test_generic_report_build(valid_report_data):
    report = Report.build(valid_report_data)
    assert isinstance(report, PredictorReport)
    assert report.json['key1'] == 'value1'


def test_predictor_report_build(valid_report_data):
    report = PredictorReport.build(valid_report_data)
    assert report.status == 'OK'


def test_predictor_report_dump(valid_report_data):
    report = PredictorReport.build(valid_report_data)
    json = report.dump()
    assert json['report']['key2'] == 'value2'

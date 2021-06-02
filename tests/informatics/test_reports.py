"""Tests reports initialization."""
from citrine.informatics.reports import PredictorReport, ModelSummary, FeatureImportanceReport, Report
from citrine.informatics.descriptors import RealDescriptor


def test_status(valid_predictor_report_data):
    """Ensure we can check the status of report generation."""
    report = Report.build(valid_predictor_report_data)
    assert report.succeeded() and not report.in_progress() and not report.failed()

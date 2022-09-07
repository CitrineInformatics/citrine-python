"""Tests reports initialization."""
from citrine.informatics.reports import PredictorReport, ModelSummary, FeatureImportanceReport, Report
from citrine.informatics.descriptors import RealDescriptor


def test_status(valid_predictor_report_data):
    """Ensure we can check the status of report generation."""
    report = Report.build(valid_predictor_report_data)
    assert report.succeeded() and not report.in_progress() and not report.failed()


def test_selection_summary(valid_predictor_report_data):
    """Ensure that we can iterate selection summary results as expected."""
    report = PredictorReport.build(valid_predictor_report_data)
    selection_summaries = [
        s.selection_summary for s in report.model_summaries if s.selection_summary is not None
    ]

    assert len(selection_summaries) > 0
    for s in selection_summaries:
        assert len(s.evaluation_results) > 0
        for result in s.evaluation_results:
            assert len(result.model_settings) > 0
            for response_key in result:
                metrics = result[response_key].metrics
                assert len(metrics) > 0

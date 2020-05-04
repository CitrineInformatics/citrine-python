"""Tests reports initialization."""
from citrine.informatics.reports import PredictorReport, ModelSummary, FeatureImportanceReport
from citrine.informatics.descriptors import RealDescriptor


def test_report_init():
    """Tests that a Report object can be constructed."""
    report = PredictorReport('ERROR', descriptors=[])
    assert report.status == 'ERROR'
    assert report.model_summaries == []
    assert report.descriptors == []


def test_model_summary_init():
    """Tests that a ModelSummary object can be constructed."""
    x = RealDescriptor('x', 0, 1)
    y = RealDescriptor('y', 0, 1)
    z = RealDescriptor('z', 0, 1)
    feat_importance = FeatureImportanceReport(output_key='z', importances={'x': 0.8, 'y': 0.2})
    ModelSummary(name='General model',
                 inputs=[x, y],
                 outputs=[z],
                 model_settings={'optimization restarts': 15, 'backpropagation': False},
                 feature_importances=[feat_importance]
                 )

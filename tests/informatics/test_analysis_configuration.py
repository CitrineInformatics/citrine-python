"""Tests the CrossValidationAnalysisConfiguration"""
import pytest

from citrine.informatics.analysis_configuration import CrossValidationAnalysisConfiguration

@pytest.fixture
def cv_conf() -> CrossValidationAnalysisConfiguration:
    return CrossValidationAnalysisConfiguration('name', 'description', 1, 3, 20, 100, ['keys'])


def test_cv_conf_initialization(cv_conf):
    """Make sure the correct fields go to the correct places."""
    assert cv_conf.name == 'name'
    assert cv_conf.description == 'description'
    assert cv_conf.n_folds == 1
    assert cv_conf.n_trials == 3
    assert cv_conf.max_rows == 20
    assert cv_conf.seed == 100
    assert cv_conf.group_by_keys == ['keys']
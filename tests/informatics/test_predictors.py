"""Tests for citrine.informatics.processors."""
import mock
import pytest
import uuid

from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import ParaboloidPredictor, SimpleMLPredictor

x = RealDescriptor("x", 0, 100, "")
y = RealDescriptor("y", 0, 100, "")
z = RealDescriptor("z", 0, 100, "")


@pytest.fixture
def paraboloid_predictor() -> ParaboloidPredictor:
    """Build a ParaboloidPredictor for testing."""
    return ParaboloidPredictor('my thing', 'does a thing', [x, y], z)

@pytest.fixture
def legacy_predictor() -> SimpleMLPredictor:
    """Build a ParaboloidPredictor for testing."""
    return SimpleMLPredictor(name='ML predictor',
                             description='Predicts z from input x and latent variable y',
                             inputs=[x],
                             outputs=[z],
                             latent_variables=[y],
                             training_data='training_data_key')


def test_paraboloid_initialization(paraboloid_predictor):
    """Make sure the correct fields go to the correct places for the ParaboloidPredictor."""
    assert paraboloid_predictor.name == 'my thing'
    assert paraboloid_predictor.description == 'does a thing'
    assert paraboloid_predictor.input_keys == [x, y]
    assert paraboloid_predictor.output_key == z
    assert str(paraboloid_predictor) == '<ParaboloidPredictor \'my thing\'>'
    assert not hasattr(paraboloid_predictor, 'report')


def test_legacy_initialization(legacy_predictor):
    """Make sure the correct fields go to the correct places for the Simple Predictor."""
    assert legacy_predictor.name == 'ML predictor'
    assert legacy_predictor.description == 'Predicts z from input x and latent variable y'
    assert len(legacy_predictor.inputs) == 1
    assert legacy_predictor.inputs[0] == x
    assert len(legacy_predictor.outputs) == 1
    assert legacy_predictor.outputs[0] == z
    assert len(legacy_predictor.latent_variables) == 1
    assert legacy_predictor.latent_variables[0] == y
    assert legacy_predictor.training_data == 'training_data_key'
    assert str(legacy_predictor) == '<SimplePredictor \'ML predictor\'>'
    assert hasattr(legacy_predictor, 'report')


def test_parabaloid_post_build(paraboloid_predictor):
    """Ensures we can run post_build on a parabaloid predictor"""
    assert paraboloid_predictor.post_build(uuid.uuid4(), dict()) is None


def test_legacy_post_build(legacy_predictor):
    """Ensures we get a report from a legacy predictor post_build call"""
    assert legacy_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    legacy_predictor.session = session
    legacy_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert legacy_predictor.report is not None
    assert legacy_predictor.report.status == 'OK'

"""Tests for citrine.informatics.processors."""
import mock
import pytest
import uuid

from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import SimpleMLPredictor

x = RealDescriptor("x", 0, 100, "")
y = RealDescriptor("y", 0, 100, "")
z = RealDescriptor("z", 0, 100, "")


@pytest.fixture
def simple_predictor() -> SimpleMLPredictor:
    """Build a SimpleMLPredictor for testing."""
    return SimpleMLPredictor(name='ML predictor',
                             description='Predicts z from input x and latent variable y',
                             inputs=[x],
                             outputs=[z],
                             latent_variables=[y],
                             training_data='training_data_key')


def test_simple_initialization(simple_predictor):
    """Make sure the correct fields go to the correct places for the Simple Predictor."""
    assert simple_predictor.name == 'ML predictor'
    assert simple_predictor.description == 'Predicts z from input x and latent variable y'
    assert len(simple_predictor.inputs) == 1
    assert simple_predictor.inputs[0] == x
    assert len(simple_predictor.outputs) == 1
    assert simple_predictor.outputs[0] == z
    assert len(simple_predictor.latent_variables) == 1
    assert simple_predictor.latent_variables[0] == y
    assert simple_predictor.training_data == 'training_data_key'
    assert str(simple_predictor) == '<SimplePredictor \'ML predictor\'>'
    assert hasattr(simple_predictor, 'report')


def test_simple_post_build(simple_predictor):
    """Ensures we get a report from a simple predictor post_build call"""
    assert simple_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    simple_predictor.session = session
    simple_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert simple_predictor.report is not None
    assert simple_predictor.report.status == 'OK'

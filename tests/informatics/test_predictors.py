"""Tests for citrine.informatics.processors."""
import pytest

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

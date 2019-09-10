"""Tests for citrine.informatics.processors serialization."""
import pytest
import uuid

from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import Predictor, ParaboloidPredictor, SimpleMLPredictor

x = RealDescriptor("x", 0, 100, "")
y = RealDescriptor("y", 0, 100, "")
z = RealDescriptor("z", 0, 100, "")


@pytest.fixture
def valid_paraboloid_data():
    """Produce valid data used for these tests."""
    return dict(
        status='INVALID',
        status_info=['Something is wrong', 'Very wrong'],
        display_name='my predictor',
        schema_id='ff26b280-8a8b-46ab-b7aa-0c73ff84b0fd',
        id=str(uuid.uuid4()),
        config=dict(
            type='Paraboloid',
            name='my predictor',
            description='does some things',
            inputs=[x.dump(), y.dump()],
            output=z.dump()
        )
    )


@pytest.fixture
def valid_simple_ml_data():
    """Produce valid data used for these tests."""
    return dict(
        status='VALID',
        status_info=[],
        display_name='ML predictor',
        schema_id='08d20e5f-e329-4de0-a90a-4b5e36b91703',
        id=str(uuid.uuid4()),
        config=dict(
            type='Simple',
            name='ML predictor',
            description='Predicts z from input x and latent variable y',
            inputs=[x.dump()],
            outputs=[z.dump()],
            latent_variables=[y.dump()],
            training_data='training_data_key'
        )
    )


def valid_serialization_output(data):
    return {x: y for x, y in data.items() if x not in {'status', 'status_info'}}


def test_simple_paraboloid_deserialization(valid_paraboloid_data):
    """Ensure that a deserialized ParaboloidPredictor looks sane."""
    predictor: ParaboloidPredictor = ParaboloidPredictor.build(valid_paraboloid_data)
    assert predictor.name == 'my predictor'
    assert predictor.description == 'does some things'
    assert predictor.input_keys[0] == x
    assert predictor.input_keys[1] == y
    assert predictor.output_key == z


def test_polymorphic_paraboloid_deserialization(valid_paraboloid_data):
    """Ensure that a polymorphically deserialized ParaboloidPredictor looks sane."""
    predictor: ParaboloidPredictor = Predictor.build(valid_paraboloid_data)
    assert predictor.name == 'my predictor'
    assert predictor.description == 'does some things'
    assert predictor.input_keys[0] == x
    assert predictor.input_keys[1] == y
    assert predictor.output_key == z


def test_paraboloid_serialization(valid_paraboloid_data):
    """Ensure that a serialized ParaboloidPredictor looks sane."""
    predictor = ParaboloidPredictor.build(valid_paraboloid_data)
    serialized = predictor.dump()
    serialized['id'] = valid_paraboloid_data['id']
    assert serialized == valid_serialization_output(valid_paraboloid_data)


def test_simple_legacy_deserialization(valid_simple_ml_data):
    """Ensure that a deserialized SimplePredictor looks sane."""
    predictor: SimpleMLPredictor = SimpleMLPredictor.build(valid_simple_ml_data)
    assert predictor.name == 'ML predictor'
    assert predictor.description == 'Predicts z from input x and latent variable y'
    assert len(predictor.inputs) == 1
    assert predictor.inputs[0] == x
    assert len(predictor.outputs) == 1
    assert predictor.outputs[0] == z
    assert len(predictor.latent_variables) == 1
    assert predictor.latent_variables[0] == y
    assert predictor.training_data == 'training_data_key'


def test_polymorphic_legacy_deserialization(valid_simple_ml_data):
    """Ensure that a polymorphically deserialized SimplePredictor looks sane."""
    predictor: SimpleMLPredictor = Predictor.build(valid_simple_ml_data)
    assert predictor.name == 'ML predictor'
    assert predictor.description == 'Predicts z from input x and latent variable y'
    assert len(predictor.inputs) == 1
    assert predictor.inputs[0] == x
    assert len(predictor.outputs) == 1
    assert predictor.outputs[0] == z
    assert len(predictor.latent_variables) == 1
    assert predictor.latent_variables[0] == y
    assert predictor.training_data == 'training_data_key'


def test_legacy_serialization(valid_simple_ml_data):
    """Ensure that a serialized SimplePredictor looks sane."""
    predictor = SimpleMLPredictor.build(valid_simple_ml_data)
    serialized = predictor.dump()
    serialized['id'] = valid_simple_ml_data['id']
    assert serialized == valid_serialization_output(valid_simple_ml_data)

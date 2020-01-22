"""Tests for citrine.informatics.predictors serialization."""
import pytest
from uuid import UUID

from citrine.informatics.predictors import ExpressionPredictor, GraphPredictor, Predictor, SimpleMLPredictor
from citrine.informatics.descriptors import RealDescriptor


def valid_serialization_output(data):
    return {x: y for x, y in data.items() if x not in {'status', 'status_info'}}


def test_simple_legacy_deserialization(valid_simple_ml_predictor_data):
    """Ensure that a deserialized SimplePredictor looks sane."""
    predictor: SimpleMLPredictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    assert predictor.name == 'ML predictor'
    assert predictor.description == 'Predicts z from input x and latent variable y'
    assert len(predictor.inputs) == 1
    assert predictor.inputs[0] == RealDescriptor("x", 0, 100, "")
    assert len(predictor.outputs) == 1
    assert predictor.outputs[0] == RealDescriptor("z", 0, 100, "")
    assert len(predictor.latent_variables) == 1
    assert predictor.latent_variables[0] == RealDescriptor("y", 0, 100, "")
    assert predictor.training_data.table_id == UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762')


def test_polymorphic_legacy_deserialization(valid_simple_ml_predictor_data):
    """Ensure that a polymorphically deserialized SimplePredictor looks sane."""
    predictor: SimpleMLPredictor = Predictor.build(valid_simple_ml_predictor_data)
    assert predictor.name == 'ML predictor'
    assert predictor.description == 'Predicts z from input x and latent variable y'
    assert len(predictor.inputs) == 1
    assert predictor.inputs[0] == RealDescriptor("x", 0, 100, "")
    assert len(predictor.outputs) == 1
    assert predictor.outputs[0] == RealDescriptor("z", 0, 100, "")
    assert len(predictor.latent_variables) == 1
    assert predictor.latent_variables[0] == RealDescriptor("y", 0, 100, "")
    assert predictor.training_data.table_id == UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762')


def test_legacy_serialization(valid_simple_ml_predictor_data):
    """Ensure that a serialized SimplePredictor looks sane."""
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    serialized = predictor.dump()
    serialized['id'] = valid_simple_ml_predictor_data['id']
    assert serialized == valid_serialization_output(valid_simple_ml_predictor_data)


def test_graph_serialization(valid_graph_predictor_data):
    """Ensure that a serialized GraphPredictor looks sane."""
    predictor = GraphPredictor.build(valid_graph_predictor_data)
    serialized = predictor.dump()
    serialized['id'] = valid_graph_predictor_data['id']
    assert serialized == valid_serialization_output(valid_graph_predictor_data)


def test_expression_serialization(valid_expression_predictor_data):
    """Ensure that a serialized ExpressionPredictor looks sane."""
    predictor = ExpressionPredictor.build(valid_expression_predictor_data)
    serialized = predictor.dump()
    serialized['id'] = valid_expression_predictor_data['id']
    assert serialized == valid_serialization_output(valid_expression_predictor_data)


def test_invalid_predictor_type(invalid_predictor_data):
    """Ensures we raise proper exception when an invalid type is used."""
    with pytest.raises(ValueError):
        Predictor.build(invalid_predictor_data)

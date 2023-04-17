"""Tests for citrine.informatics.predictors serialization."""
from copy import deepcopy
from uuid import UUID

import pytest

from . import predictor_serialization_check, valid_serialization_output, \
    predictor_node_serialization_check
from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import *


def test_auto_ml_deserialization(valid_auto_ml_predictor_data):
    """Ensure that a deserialized SimplePredictor looks sane."""
    predictor: AutoMLPredictor = AutoMLPredictor.build(valid_auto_ml_predictor_data)
    assert predictor.name == 'AutoML predictor'
    assert predictor.description == 'Predicts z from input x'
    assert len(predictor.inputs) == 1
    assert predictor.inputs[0] == RealDescriptor("x", lower_bound=0, upper_bound=100, units="")
    assert len(predictor.outputs) == 1
    assert predictor.outputs[0] == RealDescriptor("z", lower_bound=0, upper_bound=100, units="")
    assert len(predictor.training_data) == 0


def test_polymorphic_auto_ml_deserialization(valid_auto_ml_predictor_data):
    """Ensure that a polymorphically deserialized SimplePredictor looks sane."""
    predictor: AutoMLPredictor = PredictorNode.build(valid_auto_ml_predictor_data)
    assert predictor.name == 'AutoML predictor'
    assert predictor.description == 'Predicts z from input x'
    assert len(predictor.inputs) == 1
    assert predictor.inputs[0] == RealDescriptor("x", lower_bound=0, upper_bound=100, units="")
    assert len(predictor.outputs) == 1
    assert predictor.outputs[0] == RealDescriptor("z", lower_bound=0, upper_bound=100, units="")
    assert len(predictor.training_data) == 0


def test_legacy_serialization(valid_auto_ml_predictor_data):
    """Ensure that a serialized SimplePredictor looks sane."""
    predictor_node_serialization_check(valid_auto_ml_predictor_data, AutoMLPredictor)


def test_graph_serialization(valid_graph_predictor_data):
    """Ensure that a serialized GraphPredictor looks sane."""
    graph_data_copy = deepcopy(valid_graph_predictor_data)
    predictor = GraphPredictor.build(valid_graph_predictor_data)
    serialized = predictor.dump()
    assert serialized['instance']['predictors'] == graph_data_copy['data']['instance']['predictors']
    assert serialized == valid_serialization_output(graph_data_copy['data'])


def test_expression_serialization(valid_expression_predictor_data):
    """Ensure that a serialized ExpressionPredictor looks sane."""
    predictor_node_serialization_check(valid_expression_predictor_data, ExpressionPredictor)


def test_ing_to_formulation_serialization(valid_ing_formulation_predictor_data):
    """Ensure that a serialized IngredientsToFormulationPredictor looks sane."""
    predictor_node_serialization_check(valid_ing_formulation_predictor_data, IngredientsToFormulationPredictor)


def test_mean_property_serialization(valid_mean_property_predictor_data):
    """Ensure that a serialized MeanPropertyPredictor looks sane."""
    predictor_node_serialization_check(valid_mean_property_predictor_data, MeanPropertyPredictor)


def test_simple_mixture_predictor_serialization(valid_simple_mixture_predictor_data):
    predictor_node_serialization_check(valid_simple_mixture_predictor_data, SimpleMixturePredictor)


def test_label_fractions_serialization(valid_label_fractions_predictor_data):
    """Ensure that a serialized LabelFractionPredictor looks sane."""
    predictor_node_serialization_check(valid_label_fractions_predictor_data, LabelFractionsPredictor)


def test_ingredient_fractions_serialization(valid_ingredient_fractions_predictor_data):
    """"Ensure that a serialized IngredientsFractionsPredictor looks sane."""
    predictor_node_serialization_check(valid_ingredient_fractions_predictor_data, IngredientFractionsPredictor)


def test_auto_ml_serialization(valid_auto_ml_predictor_data):
    """"Ensure that a serialized AutoMLPredictor looks sane."""
    predictor_node_serialization_check(valid_auto_ml_predictor_data, AutoMLPredictor)


def test_invalid_graph(invalid_graph_predictor_data):
    """Ensures we raise proper exception when horribly malformed data is used."""
    with pytest.raises(ValueError):
        GraphPredictor.build(invalid_graph_predictor_data)


def test_invalid_predictor_node_type(invalid_predictor_node_data):
    """Ensures we raise proper exception when an invalid type is used."""
    with pytest.raises(ValueError):
        PredictorNode.build(invalid_predictor_node_data)

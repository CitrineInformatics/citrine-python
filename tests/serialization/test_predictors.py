"""Tests for citrine.informatics.predictors serialization."""
from copy import deepcopy
from uuid import UUID

import pytest

from . import serialization_check, valid_serialization_output
from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import ExpressionPredictor, GeneralizedMeanPropertyPredictor, \
    GraphPredictor, Predictor, SimpleMLPredictor, IngredientsToSimpleMixturePredictor, \
    LabelFractionsPredictor, SimpleMixturePredictor, IngredientFractionsPredictor, DeprecatedExpressionPredictor


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
    assert len(predictor.training_data) == 1
    assert predictor.training_data[0].table_id == UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762')


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
    assert len(predictor.training_data) == 1
    assert predictor.training_data[0].table_id == UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762')


def test_legacy_serialization(valid_simple_ml_predictor_data):
    """Ensure that a serialized SimplePredictor looks sane."""
    serialization_check(valid_simple_ml_predictor_data, SimpleMLPredictor)


def test_graph_serialization(valid_graph_predictor_data):
    """Ensure that a serialized GraphPredictor looks sane."""
    graph_data_copy = deepcopy(valid_graph_predictor_data)
    predictor = GraphPredictor.build(valid_graph_predictor_data)
    serialized = predictor.dump()
    serialized['id'] = graph_data_copy['id']
    assert serialized['config']['predictors'] == graph_data_copy['config']['predictors']
    assert serialized == valid_serialization_output(graph_data_copy)


def test_deprecated_expression_serialization(valid_deprecated_expression_predictor_data):
    """Ensure that a serialized DeprecatedExpressionPredictor looks sane."""
    serialization_check(valid_deprecated_expression_predictor_data, DeprecatedExpressionPredictor)


def test_expression_serialization(valid_expression_predictor_data):
    """Ensure that a serialized ExpressionPredictor looks sane."""
    serialization_check(valid_expression_predictor_data, ExpressionPredictor)


def test_ing_to_simple_mixture_serialization(valid_ing_to_simple_mixture_predictor_data):
    """Ensure that a serialized IngredientsToSimpleMixturePredictor looks sane."""
    serialization_check(valid_ing_to_simple_mixture_predictor_data, IngredientsToSimpleMixturePredictor)


def test_generalized_mean_property_serialization(valid_generalized_mean_property_predictor_data):
    """Ensure that a serialized GeneralizedMeanPropertyPredictor looks sane."""
    serialization_check(valid_generalized_mean_property_predictor_data, GeneralizedMeanPropertyPredictor)


def test_simple_mixture_predictor_serialization(valid_simple_mixture_predictor_data):
    serialization_check(valid_simple_mixture_predictor_data, SimpleMixturePredictor)


def test_label_fractions_serialization(valid_label_fractions_predictor_data):
    """Ensure that a serialized LabelFractionPredictor looks sane."""
    serialization_check(valid_label_fractions_predictor_data, LabelFractionsPredictor)


def test_ingredient_fractions_serialization(valid_ingredient_fractions_predictor_data):
    """"Ensure that a serialized IngredientsFractionsPredictor looks sane."""
    serialization_check(valid_ingredient_fractions_predictor_data, IngredientFractionsPredictor)


def test_invalid_predictor_type(invalid_predictor_data):
    """Ensures we raise proper exception when an invalid type is used."""
    with pytest.raises(ValueError):
        Predictor.build(invalid_predictor_data)

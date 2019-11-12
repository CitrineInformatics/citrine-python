"""Tests for citrine.informatics.design_spaces serialization."""
import uuid

import pytest

from citrine.informatics.modules import Module
from citrine.informatics.design_spaces import ProductDesignSpace
from citrine.informatics.predictors import SimpleMLPredictor
from citrine.informatics.processors import GridProcessor


def test_polymorphic_design_space_deserialization(valid_product_design_space_data):
    """Ensure that a deserialized ProductDesignSpace looks sane."""
    module: Module = Module.build(valid_product_design_space_data)
    assert type(module) == ProductDesignSpace


def test_polymorphic_predictor_deserialization(valid_simple_ml_predictor_data):
    """Ensure that a serialized ProductDesignSpace looks sane."""
    module = Module.build(valid_simple_ml_predictor_data)
    assert type(module) == SimpleMLPredictor


def test_polymorphic_processor_deserialization(valid_grid_processor_data):
    module = Module.build(valid_grid_processor_data)
    assert type(module) == GridProcessor

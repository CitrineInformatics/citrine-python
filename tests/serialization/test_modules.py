"""Tests for citrine.informatics.design_spaces serialization."""
import uuid

from citrine.informatics.modules import Module, ModuleRef
from citrine.informatics.design_spaces import ProductDesignSpace
from citrine.informatics.predictors import SimpleMLPredictor
from citrine.informatics.processors import GridProcessor


def test_polymorphic_design_space_deserialization(old_valid_product_design_space_data):
    """Ensure that a deserialized ProductDesignSpace looks sane."""
    module: Module = Module.build(old_valid_product_design_space_data)
    assert type(module) == ProductDesignSpace


def test_polymorphic_predictor_deserialization(valid_simple_ml_predictor_data):
    """Ensure that a serialized ProductDesignSpace looks sane."""
    module = Module.build(valid_simple_ml_predictor_data)
    assert type(module) == SimpleMLPredictor


def test_polymorphic_processor_deserialization(valid_grid_processor_data):
    module = Module.build(valid_grid_processor_data)
    assert type(module) == GridProcessor


def test_module_ref_serialization():
    # Given
    m_uid = uuid.uuid4()
    ref = ModuleRef(module_uid=m_uid)

    # When
    ref_data = ref.dump()

    # Then
    assert ref_data['module_uid'] == str(m_uid)
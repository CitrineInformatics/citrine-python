"""Tests for citrine.informatics.design_spaces serialization."""
from citrine.informatics.modules import Module
from citrine.informatics.design_spaces import ProductDesignSpace


def test_polymorphic_design_space_deserialization(old_valid_product_design_space_data):
    """Ensure that a deserialized ProductDesignSpace looks sane."""
    module: Module = Module.build(old_valid_product_design_space_data)
    assert type(module) == ProductDesignSpace

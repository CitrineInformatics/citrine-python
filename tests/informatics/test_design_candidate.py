"""Tests for citrine.informatics.design_candidate."""
from citrine.informatics.design_candidate import DesignVariable


def test_deser():
    """Test polymorphic deserialization of design variable"""
    dumped = {"type": "R", "m": 1.0, "s": 2.0}
    deserialized = DesignVariable.build(dumped)
    assert deserialized.mean == 1.0
    assert deserialized.std == 2.0

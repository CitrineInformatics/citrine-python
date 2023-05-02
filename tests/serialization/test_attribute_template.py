"""Tests of the attribute template schema."""
import pytest
import logging
from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.parameter_template import ParameterTemplate
from citrine.resources.property_template import PropertyTemplate
from gemd.entity.bounds.real_bounds import RealBounds
from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.bounds.categorical_bounds import CategoricalBounds
from gemd.json import loads, dumps


def test_condition_template():
    """Test creation and serde of condition templates."""
    bounds = RealBounds(2.5, 10.0, default_units='cm')
    template = ConditionTemplate("Chamber width", tags=[], bounds=bounds, description="width of chamber")
    assert template.uids is not None  # uids should be added automatically

    # Take template through a serde cycle and ensure that it is unchanged
    assert ConditionTemplate.build(template.dump()) == template

    # A more complicated cycle that goes through both gemd-python and citrine-python serde.
    assert ConditionTemplate.build(loads(dumps(template.dump())).as_dict()) == template


def test_parameter_template():
    """Test creation and serde of parameter templates."""
    bounds = IntegerBounds(-3, 8)
    template = ParameterTemplate("Position knob", bounds=bounds, tags=["Tag1", "A::B::C"])
    assert template.uids is not None  # uids should be added automatically
    assert ParameterTemplate.build(template.dump()) == template


def test_property_template():
    """Test creation and serde of condition templates."""
    bounds = CategoricalBounds(['solid', 'liquid', 'gas'])
    template = PropertyTemplate("State", bounds=bounds, uids={'my_id': '0'})
    assert PropertyTemplate.build(template.dump()) == template

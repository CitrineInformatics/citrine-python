"""Test that templates show expected behavior."""
import pytest

from citrine.resources.material_template import MaterialTemplate
from citrine.resources.measurement_template import MeasurementTemplate
from citrine.resources.process_template import ProcessTemplate
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.property_template import PropertyTemplate
from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.parameter_template import ParameterTemplate
from taurus.entity.bounds.real_bounds import RealBounds
from taurus.entity.bounds.integer_bounds import IntegerBounds
from taurus.entity.bounds.categorical_bounds import CategoricalBounds
from citrine.attributes.condition import Condition
from taurus.entity.value.nominal_real import NominalReal


def test_object_template_validation():
    """Test that attribute templates are validated against given bounds."""
    length_template = PropertyTemplate("Length", RealBounds(2.0, 3.5, 'cm'))
    dial_template = ConditionTemplate("dial", IntegerBounds(0, 5))
    color_template = ParameterTemplate("Color", CategoricalBounds(["red", "green", "blue"]))

    with pytest.raises(ValueError):
        MaterialTemplate("Block", properties=[[length_template, RealBounds(3.0, 4.0, 'cm')]])

    with pytest.raises(ValueError):
        ProcessTemplate("a process", conditions=[[color_template, CategoricalBounds(["zz"])]])
        
    with pytest.raises(ValueError):
        MeasurementTemplate("A measurement", parameters=[[dial_template, IntegerBounds(-3, -1)]])


def test_template_assignment():
    """Test that an object and its attributes can both be assigned templates."""
    humidity_template = ConditionTemplate("Humidity", RealBounds(0.5, 0.75, ""))
    template = ProcessTemplate("Dry", conditions=[[humidity_template, RealBounds(0.5, 0.65, "")]])
    ProcessSpec("Dry a polymer", template=template, conditions=[
        Condition("Humidity", value=NominalReal(0.6, ""), template=humidity_template)])
    with pytest.raises(RuntimeWarning):
        ProcessSpec("Dry a polymer", template=template, conditions=[
                   Condition("Humidity", value=NominalReal(0.7, ""))])

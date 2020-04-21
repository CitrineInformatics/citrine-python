"""Tests of the object template schema."""
from citrine.resources.material_template import MaterialTemplate
from citrine.resources.measurement_template import MeasurementTemplate
from citrine.resources.process_template import ProcessTemplate
from citrine.resources.property_template import PropertyTemplate
from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.parameter_template import ParameterTemplate
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.bounds.real_bounds import RealBounds
from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.bounds.categorical_bounds import CategoricalBounds


def test_object_template_serde():
    """Test serde of an object template."""
    length_template = PropertyTemplate("Length", RealBounds(2.0, 3.5, 'cm'))
    sub_bounds = RealBounds(2.5, 3.0, 'cm')
    color_template = PropertyTemplate("Color", CategoricalBounds(["red", "green", "blue"]))
    # Properties are a mixture of property templates and [template, bounds], pairs
    block_template = MaterialTemplate("Block", properties=[[length_template, sub_bounds],
                                                           color_template])
    copy_template = MaterialTemplate.build(block_template.dump())
    assert copy_template == block_template

    # Tests below exercise similar code, but for measurement and process templates
    pressure_template = ConditionTemplate("pressure", RealBounds(0.1, 0.11, 'MPa'))
    index_template = ParameterTemplate("index", IntegerBounds(2, 10))
    meas_template = MeasurementTemplate("A measurement of length", properties=[length_template],
                                        conditions=[pressure_template], description="Description",
                                        parameters=[index_template], tags=["foo"])
    assert MeasurementTemplate.build(meas_template.dump()) == meas_template

    proc_template = ProcessTemplate("Make an object", parameters=[index_template],
                                    conditions=[pressure_template], allowed_labels=["Label"],
                                    allowed_names=["first sample", "second sample"])
    assert ProcessTemplate.build(proc_template.dump()) == proc_template

    # Check that serde still works if the template is a LinkByUID
    proc_template.conditions[0][0] = LinkByUID('id', pressure_template.uids['id'])
    assert ProcessTemplate.build(proc_template.dump()) == proc_template

from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.measurement_spec import MeasurementSpec
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.property_template import PropertyTemplate
from citrine.seeding.sort_gems import split_templates_from_objects
from taurus.entity.bounds.categorical_bounds import CategoricalBounds


def test_no_templates():
    objs = [ProcessSpec("ps"), MeasurementSpec("ms")]
    templates, data_objects = split_templates_from_objects(objs)
    assert len(templates) == 0
    assert len(data_objects) == 2

def test_no_data_objects():
    objs = [PropertyTemplate("pt", CategoricalBounds()), ConditionTemplate("ct", CategoricalBounds())]
    templates, data_objects = split_templates_from_objects(objs)
    assert len(templates) == 2
    assert len(data_objects) == 0

def test_both_present():
    objs = [ProcessSpec("ps"),
            PropertyTemplate("pt", CategoricalBounds()),
            MeasurementSpec("ms"),
            ConditionTemplate("ct", CategoricalBounds())]
    templates, data_objects = split_templates_from_objects(objs)
    assert len(templates) == 2
    assert len(data_objects) == 2

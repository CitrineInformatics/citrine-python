import pytest
from taurus.entity.bounds.real_bounds import RealBounds

from citrine.resources.condition_template import ConditionTemplate, ConditionTemplateCollection
from citrine.resources.ingredient_run import IngredientRun, IngredientRunCollection
from citrine.resources.ingredient_spec import IngredientSpec, IngredientSpecCollection
from citrine.resources.material_spec import MaterialSpec, MaterialSpecCollection
from citrine.resources.material_template import MaterialTemplate, MaterialTemplateCollection
from citrine.resources.measurement_run import MeasurementRun, MeasurementRunCollection
from citrine.resources.measurement_spec import MeasurementSpec, MeasurementSpecCollection
from citrine.resources.measurement_template import MeasurementTemplate, MeasurementTemplateCollection
from citrine.resources.parameter_template import ParameterTemplate, ParameterTemplateCollection
from citrine.resources.process_run import ProcessRun, ProcessRunCollection
from citrine.resources.process_spec import ProcessSpec, ProcessSpecCollection
from citrine.resources.process_template import ProcessTemplate, ProcessTemplateCollection
from citrine.resources.property_template import PropertyTemplate, PropertyTemplateCollection
from citrine.resources.response import Response

resource_string_data = [
    (IngredientRun, {'name': 'foo'}, "<Ingredient run 'foo'>"),
    (IngredientSpec, {'name': 'foo'}, "<Ingredient spec 'foo'>"),
    (MaterialSpec, {'name': 'foo'}, "<Material spec 'foo'>"),
    (MaterialTemplate, {'name': 'foo'}, "<Material template 'foo'>"),
    (MeasurementRun, {'name': 'foo'}, "<Measurement run 'foo'>"),
    (MeasurementSpec, {'name': 'foo'}, "<Measurement spec 'foo'>"),
    (MeasurementTemplate, {'name': 'foo'}, "<Measurement template 'foo'>"),
    (ParameterTemplate, {'name': 'foo', 'bounds': RealBounds(0, 1, '')}, "<Parameter template 'foo'>"),
    (ProcessRun, {'name': 'foo'}, "<Process run 'foo'>"),
    (ProcessSpec, {'name': 'foo'}, "<Process spec 'foo'>"),
    (ProcessTemplate, {'name': 'foo'}, "<Process template 'foo'>"),
    (PropertyTemplate, {'name': 'foo', 'bounds': RealBounds(0, 1, '')}, "<Property template 'foo'>"),
    (ConditionTemplate, {'name': 'foo', 'bounds': RealBounds(0, 1, '')}, "<Condition template 'foo'>"),
    (Response, {'status_code': 200}, "<Response '200'>")
]

resource_type_data = [
    (IngredientRunCollection, IngredientRun),
    (IngredientSpecCollection, IngredientSpec),
    (MaterialSpecCollection, MaterialSpec),
    (MaterialTemplateCollection, MaterialTemplate),
    (MeasurementRunCollection, MeasurementRun),
    (MeasurementSpecCollection, MeasurementSpec),
    (MeasurementTemplateCollection, MeasurementTemplate),
    (ParameterTemplateCollection, ParameterTemplate),
    (ProcessRunCollection, ProcessRun),
    (ProcessSpecCollection, ProcessSpec),
    (ProcessTemplateCollection, ProcessTemplate),
    (PropertyTemplateCollection, PropertyTemplate),
    (ConditionTemplateCollection, ConditionTemplate),
]


@pytest.mark.parametrize('resource_type,kwargs,val', resource_string_data)
def test_str_representation(resource_type, kwargs, val):
    assert val == str(resource_type(**kwargs))


@pytest.mark.parametrize('collection_type,resource_type', resource_type_data)
def test_collection_type(collection_type, resource_type):
    assert resource_type == collection_type.get_type()

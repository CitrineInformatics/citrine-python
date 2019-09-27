"""Tests of the Material Run schema."""
from citrine.resources.material_run import MaterialRun
from citrine.resources.material_spec import MaterialSpec
from citrine.resources.measurement_spec import MeasurementSpec
from citrine.resources.process_run import ProcessRun
from citrine.resources.ingredient_run import IngredientRun
from citrine.resources.ingredient_spec import IngredientSpec
from citrine.resources.measurement_run import MeasurementRun
from taurus.client.json_encoder import LinkByUID
from taurus.client.json_encoder import loads, dumps
from taurus.entity.object import MeasurementRun as TaurusMeasurementRun
from taurus.entity.object import MaterialRun as TaurusMaterialRun
from taurus.entity.object import MaterialSpec as TaurusMaterialSpec
from taurus.entity.object import MeasurementSpec as TaurusMeasurementSpec
from taurus.entity.object import ProcessSpec as TaurusProcessSpec
from taurus.entity.object import ProcessRun as TaurusProcessRun
from taurus.entity.object.ingredient_spec import IngredientSpec as TaurusIngredientSpec
from taurus.entity.object.ingredient_run import IngredientRun as TaurusIngredientRun

from tests.utils.factories import MaterialRunDataFactory


def test_simple_deserialization():
    """Ensure that a deserialized Material Run looks sane."""
    valid_data: dict = MaterialRunDataFactory(name='Cake 1')
    material_run: MaterialRun = MaterialRun.build(valid_data)
    assert material_run.uids == {'id': valid_data['uids']['id']}
    assert material_run.name == 'Cake 1'
    assert material_run.tags == ["color"]
    assert material_run.notes is None
    assert material_run.process == LinkByUID('id', valid_data['process']['id'])
    assert material_run.sample_type == 'experimental'
    assert material_run.template is None
    assert material_run.spec is None
    assert material_run.file_links == []
    assert material_run.typ == 'material_run'


def test_serialization():
    """Ensure that a serialized Material Run looks sane."""
    valid_data: dict = MaterialRunDataFactory()
    material_run: MaterialRun = MaterialRun.build(valid_data)
    serialized = material_run.dump()
    assert serialized == valid_data


def test_process_attachment():
    """Test that a process can be attached to a material, and that the connection survives serde"""
    cake = MaterialRun('Final cake')
    cake.process = ProcessRun('Icing')
    cake_data = cake.dump()

    cake_copy = loads(dumps(cake_data)).as_dict()

    assert cake_copy['name'] == cake.name
    assert cake_copy['uids'] == cake.uids
    assert cake.process.uids['id'] == cake_copy['process'].uids['id']

    reconstituted_cake = MaterialRun.build(cake_copy)
    assert isinstance(reconstituted_cake, MaterialRun)
    assert isinstance(reconstituted_cake.process, ProcessRun)


def test_nested_serialization():
    """Create a bunch of nested objects and make sure that nothing breaks."""

    # helper
    def make_ingredient(material: MaterialRun):
        return IngredientRun(name=material.name, material=material)

    icing = ProcessRun(name="Icing")
    cake = MaterialRun(name='Final cake', process=icing)

    cake.process.ingredients.append(make_ingredient(MaterialRun('Baked Cake')))
    cake.process.ingredients.append(make_ingredient(MaterialRun('Frosting')))

    baked = cake.process.ingredients[0].material
    baked.process = ProcessRun(name='Baking')
    baked.process.ingredients.append(make_ingredient(MaterialRun('Batter')))

    batter = baked.process.ingredients[0].material
    batter.process = ProcessRun(name='Mixing batter')

    batter.process.ingredients.append(make_ingredient(material=MaterialRun('Butter')))
    batter.process.ingredients.append(make_ingredient(material=MaterialRun('Sugar')))
    batter.process.ingredients.append(make_ingredient(material=MaterialRun('Flour')))
    batter.process.ingredients.append(make_ingredient(material=MaterialRun('Milk')))

    cake.dump()


def test_measurement_material_connection_rehydration():
    """Test that fully-linked Taurus object can be built as fully-linked Citrine-python object."""
    starting_mat_spec = TaurusMaterialSpec("starting material")
    starting_mat = TaurusMaterialRun("starting material", spec=starting_mat_spec)
    meas_spec = TaurusMeasurementSpec("measurement spec")
    meas1 = TaurusMeasurementRun("measurement on starting material",
                                 spec=meas_spec, material=starting_mat)

    process_spec = TaurusProcessSpec("Transformative process")
    process = TaurusProcessRun("Transformative process", spec=process_spec)
    ingredient_spec = TaurusIngredientSpec(name="ingredient", material=starting_mat_spec,
                                           process=process_spec)
    ingredient = TaurusIngredientRun(name="ingredient", material=starting_mat, process=process,
                                     spec=ingredient_spec)

    ending_mat_spec = TaurusMaterialSpec("ending material", process=process_spec)
    ending_mat = TaurusMaterialRun("ending material", process=process, spec=ending_mat_spec)
    meas2 = TaurusMeasurementRun("measurement on ending material",
                                 spec=meas_spec, material=ending_mat)

    copy = MaterialRun.build(ending_mat)
    assert isinstance(copy, MaterialRun), "copy of ending_mat should be a MaterialRun"
    assert len(copy.measurements) == 1, "copy of ending_mat should have one measurement"
    assert isinstance(copy.measurements[0], MeasurementRun), \
        "copy of ending_mat should have a measurement that is a MeasurementRun"
    assert isinstance(copy.measurements[0].spec, MeasurementSpec), \
        "copy of ending_mat should have a measurement that has a spec that is a MeasurementSpec"
    assert isinstance(copy.process, ProcessRun), "copy of ending_mat should have a process"
    assert len(copy.process.ingredients) == 1, \
        "copy of ending_mat should have a process with one ingredient"
    assert isinstance(copy.spec, MaterialSpec), "copy of ending_mat should have a spec"
    assert len(copy.spec.process.ingredients) == 1, \
        "copy of ending_mat should have a spec with a process that has one ingredient"
    assert isinstance(copy.process.spec.ingredients[0], IngredientSpec), \
        "copy of ending_mat should have a spec with a process that has an ingredient " \
        "that is an IngredientRun"

    copy_ingredient = copy.process.ingredients[0]
    assert isinstance(copy_ingredient, IngredientRun), \
        "copy of ending_mat should have a process with an ingredient that is an IngredientRun"
    assert isinstance(copy_ingredient.material, MaterialRun), \
        "copy of ending_mat should have a process with an ingredient that links to a MaterialRun"
    assert len(copy_ingredient.material.measurements) == 1, \
        "copy of ending_mat should have a process with an ingredient derived from a material " \
        "that has one measurement performed on it"
    assert isinstance(copy_ingredient.material.measurements[0], MeasurementRun), \
        "copy of ending_mat should have a process with an ingredient derived from a material " \
        "that has one measurement that gets deserialized as a MeasurementRun"
    assert isinstance(copy_ingredient.material.measurements[0].spec, MeasurementSpec), \
        "copy of ending_mat should have a process with an ingredient derived from a material " \
        "that has one measurement that has a spec"

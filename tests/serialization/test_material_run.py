"""Tests of the Material Run schema."""
import pytest
from uuid import uuid4

from citrine.resources.material_run import MaterialRun
from citrine.resources.process_run import ProcessRun
from citrine.resources.ingredient_run import IngredientRun
from citrine.resources.measurement_run import MeasurementRun
from taurus.client.json_encoder import LinkByUID
from taurus.client.json_encoder import loads, dumps


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        uids={'id': str(uuid4())},
        name='Cake 1',
        tags=[],
        notes=None,
        process={'type': 'link_by_uid', 'scope': 'id', 'id': str(uuid4())},
        sample_type='experimental',
        spec=None,
        file_links=[],
        type='material_run'
    )


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized Material Run looks sane."""
    material_run: MaterialRun = MaterialRun.build(valid_data)
    assert material_run.uids == {'id': valid_data['uids']['id']}
    assert material_run.name == 'Cake 1'
    assert material_run.tags == []
    assert material_run.notes is None
    assert material_run.process == LinkByUID('id', valid_data['process']['id'])
    assert material_run.sample_type == 'experimental'
    assert material_run.template is None
    assert material_run.spec is None
    assert material_run.file_links == []
    assert material_run.typ == 'material_run'


def test_serialization(valid_data):
    """Ensure that a serialized Material Run looks sane."""
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
    icing = ProcessRun(name="Icing")
    cake = MaterialRun(name='Final cake', process=icing)

    cake.process.ingredients.append(IngredientRun(material=MaterialRun('Baked Cake')))
    cake.process.ingredients.append(IngredientRun(material=MaterialRun('Frosting')))

    baked = cake.process.ingredients[0].material
    baked.process = ProcessRun(name='Baking')
    baked.process.ingredients.append(IngredientRun(material=MaterialRun('Batter')))

    batter = baked.process.ingredients[0].material
    batter.process = ProcessRun(name='Mixing batter')

    batter.process.ingredients.append(IngredientRun(material=MaterialRun('Butter')))
    batter.process.ingredients.append(IngredientRun(material=MaterialRun('Sugar')))
    batter.process.ingredients.append(IngredientRun(material=MaterialRun('Flour')))
    batter.process.ingredients.append(IngredientRun(material=MaterialRun('Milk')))

    print(cake.dump())

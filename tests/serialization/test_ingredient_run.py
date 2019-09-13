"""Tests of the ingredient run schema."""
import pytest
from uuid import uuid4

from citrine.resources.ingredient_run import IngredientRun
from citrine.resources.material_run import MaterialRun
from taurus.entity.value.normal_real import NormalReal
from taurus.entity.value.nominal_real import NominalReal


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        uids={'id': str(uuid4())},
        tags=[],
        notes=None,
        material={'type': 'material_run', 'name': 'flour', 'uids': {'id': str(uuid4())},
                  'tags': [], 'file_links': [], 'notes': None,
                  'process': None, 'sample_type': 'unknown', 'spec': None},
        process=None,
        mass_fraction={'type': 'normal_real', 'mean': 0.5, 'std': 0.1, 'units': 'dimensionless'},
        volume_fraction=None,
        number_fraction=None,
        absolute_quantity=None,
        unique_label='flour',
        labels=['fine', 'bleached'],
        spec=None,
        file_links=[],
        type='ingredient_run'
    )


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized Ingredient Run looks sane."""
    ingredient_run: IngredientRun = IngredientRun.build(valid_data)
    assert ingredient_run.uids == {'id': valid_data['uids']['id']}
    assert ingredient_run.tags == []
    assert ingredient_run.notes is None
    assert ingredient_run.material.dump() == valid_data['material']
    assert ingredient_run.process is None
    assert ingredient_run.mass_fraction == NormalReal(0.5, 0.1, '')
    assert ingredient_run.volume_fraction is None
    assert ingredient_run.number_fraction is None
    assert ingredient_run.absolute_quantity is None
    assert ingredient_run.unique_label == 'flour'
    assert ingredient_run.labels == ['fine', 'bleached']
    assert ingredient_run.spec is None
    assert ingredient_run.file_links == []
    assert ingredient_run.typ == 'ingredient_run'


def test_serialization(valid_data):
    """Ensure that a serialized Ingredient Run looks sane."""
    ingredient_run: IngredientRun = IngredientRun.build(valid_data)
    serialized = ingredient_run.dump()
    assert serialized == valid_data


def test_material_attachment():
    """
    Attach a material run to an ingredient run.

    Check that the ingredient can be built, and that the connection survives ser/de.
    """
    flour = MaterialRun("flour", sample_type='unknown')
    flour_ingredient = IngredientRun(material=flour, absolute_quantity=NominalReal(500, 'g'),
                                     unique_label='500 g flour')

    flour_ingredient_copy = IngredientRun.build(flour_ingredient.dump())
    assert flour_ingredient_copy == flour_ingredient

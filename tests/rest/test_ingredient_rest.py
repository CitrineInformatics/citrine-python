"""Test RESTful actions on ingredient runs"""
import pytest

from citrine.resources.ingredient_run import IngredientRun
from citrine.resources.process_run import ProcessRun


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return {"type": "ingredient_run",
            "material": {"type": "link_by_uid", "id": "5c913611-c304-4254-bad2-4797c952a3b3", "scope": "ID"},
            "process": {"type": "link_by_uid", "id": "5c913611-c304-4254-bad2-4797c952a3b4", "scope": "ID"},
            "spec": {"type": "link_by_uid", "id": "5c913611-c304-4254-bad2-4797c952a3b5", "scope": "ID"},
            "name": "Good Ingredient Run",
            "labels": [],
            "mass_fraction": {'nominal': 0.5, 'units': 'dimensionless', 'type': 'nominal_real'},
            "volume_fraction": None,
            "number_fraction": None,
            "absolute_quantity": {'nominal': 2, 'units': 'g', 'type': 'nominal_real'},
            "uids": {
                "id": "09145273-1ff2-4fbd-ba56-404c0408eb49"
            },
            "tags": [],
            "notes": "Ingredients!",
            "file_links": []
            }


def test_ingredient_build(valid_data):
    """Test that an ingredient run can be built from a valid dictionary."""
    obj = IngredientRun.build(valid_data)
    assert isinstance(obj, IngredientRun)
    assert obj.material is not None
    assert obj.process is not None
    assert obj.spec is not None
    assert obj.name is not None
    assert obj.mass_fraction is not None
    assert obj.volume_fraction is None


def test_bad_type():
    """Test that a type mismatch raises an exception."""
    with pytest.raises(ValueError, match=ProcessRun.typ):
        IngredientRun.build({"type": ProcessRun.typ, "name": "Process"})

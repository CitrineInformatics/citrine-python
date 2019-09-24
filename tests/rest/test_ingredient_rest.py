"""Test RESTful actions on ingredient runs"""
import pytest

from citrine.resources.ingredient_run import IngredientRun


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return {"type": "ingredient_run", "material":
        {"type": "link_by_uid", "id": "5c913611-c304-4254-bad2-4797c952a3b3", "scope": "ID"},
            "spec": None, "name": "Good Ingredient Run", "labels": [],
            "mass_fraction": None, "volume_fraction": None, "number_fraction": None,
            "absolute_quantity": None,
            "uids": {
                "id": "09145273-1ff2-4fbd-ba56-404c0408eb49"
            },
            "tags": [],
            "notes": "Ingredients!",
            "file_links": []
            }


def test_ingredient_build(valid_data):
    """Test that an ingredient run can be built from a valid dictionary."""
    IngredientRun.build(valid_data)

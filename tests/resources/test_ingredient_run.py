from uuid import UUID

import pytest

from citrine.resources.ingredient_run import IngredientRunCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> IngredientRunCollection:
    return IngredientRunCollection(
        dataset_id=UUID("8da51e93-8b55-4dd3-8489-af8f65d4ad9a"),
        session=session,
        team_id=UUID("6b608f78-e341-422c-8076-35adc8828000"),
    )


def test_list_by_spec(collection: IngredientRunCollection):
    run_noop_gemd_relation_search_test(
        search_for="ingredient-runs",
        search_with="ingredient-specs",
        collection=collection,
        search_fn=collection.list_by_spec,
    )


def test_list_by_material(collection: IngredientRunCollection):
    run_noop_gemd_relation_search_test(
        search_for="ingredient-runs",
        search_with="material-runs",
        collection=collection,
        search_fn=collection.list_by_material,
    )


def test_list_by_process(collection: IngredientRunCollection):
    run_noop_gemd_relation_search_test(
        search_for="ingredient-runs",
        search_with="process-runs",
        collection=collection,
        search_fn=collection.list_by_process,
    )


def test_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from gemd.entity.object import IngredientRun as GEMDIngredientRun
    from gemd.entity.value import NominalReal

    from citrine.resources.ingredient_run import IngredientRun as CitrineIngredientRun

    gemd_obj = GEMDIngredientRun(
        mass_fraction=NominalReal(1.0, ""), notes="I have notes", tags=["tag!"]
    )
    citrine_obj = CitrineIngredientRun(
        mass_fraction=NominalReal(1.0, ""), notes="I have notes", tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.notes = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"


def test_name_and_labels_precedence():
    """An ingredient run's own name and labels take precedence over the spec's."""
    from citrine.resources.ingredient_run import IngredientRun as CitrineIngredientRun
    from citrine.resources.ingredient_spec import IngredientSpec

    bare = CitrineIngredientRun()
    assert bare.name is None
    assert bare.labels is None

    spec = IngredientSpec(name="flour", labels=["dry"], uids={"id": "spec"})
    run = CitrineIngredientRun(spec=spec, uids={"id": "run"})
    assert run.name == "flour"
    assert run.labels == ["dry"]
    assert run.dump()["name"] is None, "Only the run's own name is serialized"
    assert run.dump()["labels"] is None, "Only the run's own labels are serialized"

    run.name = "bleached flour"
    run.labels = ["dry", "white"]
    assert run.name == "bleached flour"
    assert run.labels == ["dry", "white"]
    built = CitrineIngredientRun.build(run.dump())
    assert built.name == "bleached flour"
    assert built.labels == ["dry", "white"]

    run.name = None
    run.labels = None
    assert run.name == "flour"
    assert run.labels == ["dry"]

    own = CitrineIngredientRun(name="salt", labels=["mineral"], spec=spec)
    assert own.name == "salt"
    assert own.labels == ["mineral"]

    with pytest.raises(TypeError):
        run.name = 5

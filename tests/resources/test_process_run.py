from uuid import UUID

import pytest

from citrine.resources.process_run import ProcessRunCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> ProcessRunCollection:
    return ProcessRunCollection(
        dataset_id=UUID("8da51e93-8b55-4dd3-8489-af8f65d4ad9a"),
        team_id=UUID("6b608f78-e341-422c-8076-35adc8828000"),
        session=session,
    )


def test_list_by_spec(collection: ProcessRunCollection):
    run_noop_gemd_relation_search_test(
        search_for="process-runs",
        search_with="process-specs",
        collection=collection,
        search_fn=collection.list_by_spec,
    )


def test_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from gemd.entity.object import ProcessRun as GEMDProcessRun

    from citrine.resources.process_run import ProcessRun as CitrineProcessRun

    gemd_obj = GEMDProcessRun(name="My Name", notes="I have notes", tags=["tag!"])
    citrine_obj = CitrineProcessRun(name="My Name", notes="I have notes", tags=["tag!"])
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.notes = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"


def test_template_round_trip():
    """A run's own template takes precedence over the spec's and survives dump and build."""
    from gemd.entity.link_by_uid import LinkByUID

    from citrine.resources.process_run import ProcessRun as CitrineProcessRun
    from citrine.resources.process_spec import ProcessSpec
    from citrine.resources.process_template import ProcessTemplate

    spec_template = ProcessTemplate("spec template", uids={"id": "spec-template"})
    spec = ProcessSpec("spec", uids={"id": "spec"}, template=spec_template)
    run = CitrineProcessRun("run", uids={"id": "run"}, spec=spec)
    assert run.template == spec_template
    assert run.dump()["template"] is None

    link = LinkByUID("id", "own-template")
    run.template = link
    assert run.template == link
    built = CitrineProcessRun.build(run.dump())
    assert built.template == link

    with pytest.raises(TypeError):
        run.template = spec

from collections.abc import Iterator
from uuid import uuid4, UUID

import pytest

from gemd.entity.dict_serializable import DictSerializable
from gemd.entity.template import ProcessTemplate as GEMDTemplate
from gemd.entity.link_by_uid import LinkByUID

from citrine.resources.audit_info import AuditInfo
from citrine.resources.data_concepts import DataConcepts, _make_link_by_uid, CITRINE_SCOPE, DataConceptsCollection
from citrine.resources.process_run import ProcessRun
from citrine.resources.process_spec import ProcessSpec, ProcessSpecCollection
from tests.utils.session import FakeCall, FakeSession


def run_noop_gemd_relation_search_test(search_for, search_with, collection, search_fn, per_page=100):
    """Test that relation searches hit the correct endpoint."""
    collection.session.set_response({'contents': []})
    test_id = 'foo-id'
    test_scope = 'foo-scope'
    result = search_fn(LinkByUID(id=test_id, scope=test_scope))
    if isinstance(result, Iterator):
        # evaluate iterator to make calls happen
        list(result)
    assert collection.session.num_calls == 1
    assert collection.session.last_call == FakeCall(
        method="GET",
        path="teams/{}/{}/{}/{}/{}".format(collection.team_id, search_with, test_scope, test_id, search_for),
        params={"dataset_id": str(collection.dataset_id), "forward": True, "ascending": True, "per_page": per_page}
    )

def test_deprication_of_positional_arguments():
    session = FakeSession()
    team_id = UUID('6b608f78-e341-422c-8076-35adc8828000')
    check_project = {'project': {'team': {'id': team_id}}}
    session.set_response(check_project)
    with pytest.deprecated_call():
        ProcessSpecCollection(uuid4(), uuid4(), session)
    with pytest.raises(TypeError):
        ProcessSpecCollection(project_id=uuid4(), dataset_id=uuid4(), session=None)

def test_assign_audit_info():
    """Test that audit_info can be injected with build but not set"""

    assert ProcessSpec("Spec with no audit info").audit_info is None, \
        "Audit info should be None by default"

    audit_info_dict = {'created_by': str(uuid4()), 'created_at': 1560033807392}
    audit_info_obj = AuditInfo.build(audit_info_dict)

    sample_object = ProcessSpec.build({
        'type': 'process_spec',
        'name': "A process spec",
        "audit_info": audit_info_dict
    })
    assert sample_object.audit_info == audit_info_obj, "Audit info should be built from a dict"

    another_object = ProcessSpec.build({
        'type': 'process_spec', 'name': "A process spec", "audit_info": audit_info_obj
    })
    assert another_object.audit_info == audit_info_obj, "Audit info should be built from an obj"

    with pytest.raises(AttributeError, match=r"can't set attribute|has no setter"):
        sample_object.audit_info = None

    with pytest.raises(ValueError, match=r"is not one of valid types.*audit_info"):
        ProcessSpec.build({
            'type': 'process_spec',
            'name': "A process spec",
            "audit_info": "Created by me, yesterday"
        })


def test_make_link_by_uid():
    """Test that _make_link_by_uid convenience method works."""
    uid = uuid4()
    expected_link = LinkByUID(scope=CITRINE_SCOPE, id=str(uid))
    spec = ProcessSpec("spec", uids={"custom scope": "custom id", CITRINE_SCOPE: str(uid)})
    assert _make_link_by_uid(spec) == expected_link
    assert _make_link_by_uid(expected_link) == expected_link
    assert _make_link_by_uid(uid) == expected_link
    assert _make_link_by_uid(str(uid)) == expected_link

    # If there's no Citrine ID, use an available ID
    no_citrine_id = ProcessSpec("spec", uids={"custom scope": "custom id"})
    assert _make_link_by_uid(no_citrine_id) == LinkByUID(scope="custom scope", id="custom id")

    with pytest.raises(ValueError):
        _make_link_by_uid(ProcessSpec("spec"))  # no ids
    with pytest.raises(TypeError):
        _make_link_by_uid(7)  # not a valid type


def test_get_type():
    """Test that get_type works, even though its not used in DataConcepts.build"""

    assert DataConcepts.get_type({"type": "process_run"}) == ProcessRun
    assert DataConcepts.get_type(ProcessSpec("foo")) == ProcessSpec

from collections.abc import Iterator

import pytest
from uuid import uuid4

from citrine.resources.audit_info import AuditInfo
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.process_run import ProcessRun
from citrine.resources.process_spec import ProcessSpec
from tests.utils.session import FakeCall


def run_noop_gemd_relation_search_test(search_for, search_with, collection, search_fn, per_page=100):
    """Test that relation searches hit the correct endpoint."""
    collection.session.set_response({'contents': []})
    test_id = 'foo-id'
    test_scope = 'foo-scope'
    result = search_fn(test_id, scope=test_scope)
    if isinstance(result, Iterator):
        # evaluate iterator to make calls happen
        list(result)
    assert collection.session.num_calls == 1
    assert collection.session.last_call == FakeCall(
        method="GET",
        path="projects/{}/{}/{}/{}/{}".format(collection.project_id, search_with, test_scope, test_id, search_for),
        params={"dataset_id": str(collection.dataset_id), "forward": True, "ascending": True, "per_page": per_page}
    )


def test_assign_audit_info():
    """Test that audit_info can be injected with build but not set"""

    assert ProcessSpec("Spec with no audit info").audit_info is None,\
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

    with pytest.raises(AttributeError, message="Audit info cannot be set"):
        sample_object.audit_info = None

    with pytest.raises(TypeError, message="Audit info must be dict or obj valued"):
        ProcessSpec.build({
            'type': 'process_spec',
            'name': "A process spec",
            "audit_info": "Created by me, yesterday"
        })


def test_get_type():
    """Test that get_type works, even though its not used in DataConcepts.build"""

    assert DataConcepts.get_type({"type": "process_run"}) == ProcessRun
    assert DataConcepts.get_type(ProcessSpec("foo")) == ProcessSpec

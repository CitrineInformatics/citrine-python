import pytest
from uuid import uuid4

from citrine._serialization.serializable import Serializable
from citrine.resources.audit_info import AuditInfo
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.process_run import ProcessRun
from citrine.resources.process_spec import ProcessSpec


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

import pytest
from uuid import uuid4

from citrine.resources.audit_info import AuditInfo
from citrine.resources.process_spec import ProcessSpec


def test_assign_audit_info():
    assert ProcessSpec("Spec with no audit info").audit_info is None

    audit_info_dict = {'created_by': str(uuid4()), 'created_at': 1560033807392}
    audit_info_obj = AuditInfo.build(audit_info_dict)
    process_spec_dict = {'type': 'process_spec', 'name': "A process spec", "audit_info": audit_info_dict}
    sample_object = ProcessSpec.build(process_spec_dict)
    assert sample_object.audit_info == audit_info_obj

    another_object = ProcessSpec.build({
        'type': 'process_spec', 'name': "A process spec", "audit_info": audit_info_obj
    })
    assert sample_object.audit_info == another_object.audit_info

    with pytest.raises(AttributeError):
        sample_object.audit_info = None

    with pytest.raises(TypeError):
        ProcessSpec.build({
            'type': 'process_spec',
            'name': "A process spec",
            "audit_info": "Created by me, yesterday"
        })

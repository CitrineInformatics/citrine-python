import pytest
from uuid import uuid4

from citrine.resources.audit_info import AuditInfo
from citrine.resources.storable import Storable
from citrine.resources.process_spec import ProcessSpec


def test_assign_audit_info():
    sample_object = ProcessSpec("A process spec")
    assert isinstance(sample_object, Storable)
    audit_info_dict = {'created_by': str(uuid4()), 'created_at': 1560033807392}
    audit_info_obj = AuditInfo.build(audit_info_dict)

    sample_object.audit_info = None
    assert sample_object.audit_info is None

    sample_object.audit_info = audit_info_dict
    assert sample_object.audit_info == audit_info_obj

    sample_object.audit_info = audit_info_obj
    assert sample_object.audit_info == audit_info_obj

    with pytest.raises(TypeError):
        sample_object.audit_info = "Created by me, yesterday"

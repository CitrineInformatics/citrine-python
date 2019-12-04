from uuid import uuid4
from datetime import datetime

from citrine.resources.audit_info import AuditInfo


def test_audit_info_str():
    audit_info_full = AuditInfo(uuid4(), datetime.now(), uuid4(), datetime.now())
    audit_info_part = AuditInfo(uuid4(), datetime.now())
    assert 'Updated by' in str(audit_info_full) and 'Created by' in str(audit_info_full)
    assert 'Updated by' not in str(audit_info_part) and 'Created by' in str(audit_info_part)

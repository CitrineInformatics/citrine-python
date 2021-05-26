from uuid import uuid4
from datetime import datetime

from citrine.resources.audit_info import AuditInfo


def test_audit_info_str():
    audit_info_full = AuditInfo.build({
        "created_by": str(uuid4()),
        "created_at": 1559933807392,
        "updated_by": str(uuid4()),
        "updated_at": 1559933807392
    })
    audit_info_part = AuditInfo.build({
        "created_by": str(uuid4()),
        "created_at": 1559933807392
    })
    assert 'Updated by' in str(audit_info_full) and 'Created by' in str(audit_info_full)
    assert 'Updated by' not in str(audit_info_part) and 'Created by' in str(audit_info_part)

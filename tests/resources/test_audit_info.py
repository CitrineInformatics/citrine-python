from citrine.resources.audit_info import AuditInfo


def test_audit_info_str():
    audit_info_full = AuditInfo('user1', 1562338832488, 'user2', 1562358832488)
    audit_info_part = AuditInfo('user1', 1562338832488)
    assert 'Updated by' in str(audit_info_full) and 'Created by' in str(audit_info_full)
    assert 'Updated by' not in str(audit_info_part) and 'Created by' in str(audit_info_part)

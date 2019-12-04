from citrine.resources.data_concepts import DataConcepts
from citrine.resources.audit_info import AuditInfo


class Storable(DataConcepts):
    """
    Data concepts objects that are stored in the data service.

    Attributes
    ----------
    audit_info: AuditInfo
        Holds platform-related metadata: when the object was created, who created it,
        when the object was most recently updated, and who most recently updated it.

    """

    _client_keys = ["audit_info"]

    @property
    def audit_info(self):
        """Get the audit info object."""
        return self._audit_info

    @audit_info.setter
    def audit_info(self, audit_info):
        if audit_info is None:
            self._audit_info = None
        elif isinstance(audit_info, AuditInfo):
            self._audit_info = audit_info
        elif isinstance(audit_info, dict):
            self._audit_info = AuditInfo.build(audit_info)
        else:
            raise TypeError("Audit Info must be a dictionary or an AuditInfo object")

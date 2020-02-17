from typing import Optional

from citrine.resources.data_concepts import DataConcepts
from citrine.resources.audit_info import AuditInfo
from taurus.entity.dict_serializable import DictSerializable


class Storable(DataConcepts, DictSerializable):
    """
    Data concepts objects that are stored in the data service.

    """

    _client_keys = ["audit_info"]

    def __init__(self, typ: str):
        DataConcepts.__init__(self, typ)
        self._audit_info = None
        self.skip.add("audit_info")

    @property
    def audit_info(self):
        """Get the audit info object."""
        return self._audit_info

    @classmethod
    def from_dict(cls, d: dict):
        audit_info = d.pop("audit_info", None)
        obj = super().from_dict(d)
        obj.skip.add("_audit_info")

        if audit_info is None:
            obj._audit_info = None
        elif isinstance(audit_info, AuditInfo):
            obj._audit_info = audit_info
        elif isinstance(audit_info, dict):
            obj._audit_info = AuditInfo.build(audit_info)
        else:
            raise TypeError("Audit Info must be a dictionary or an AuditInfo object")

        return obj

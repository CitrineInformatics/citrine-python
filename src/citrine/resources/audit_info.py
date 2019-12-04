from typing import Optional
import arrow


class AuditInfo:
    """
    Model that holds audit metadata. AuditInfo objects should not be created by the user.

    Parameters
    ----------
    created_by: str
        ID of the user who created the object
    created_at: int
        Time, in ms since epoch, at which the object was created
    updated_by: Optional[str]
        ID of the user who most recently updated the object
    updated_at: Optional[int]
        Time, in ms since epoch, at which the object was most recently updated

    """

    def __init__(self, created_by: str, created_at: int,
                 updated_by: Optional[str] = None, updated_at: Optional[int] = None):
        self.created_by = created_by
        self.created_at = created_at
        self.updated_by = updated_by
        self.updated_at = updated_at

    def __str__(self):
        create_str = 'Created by user {} at time {}'.format(
            self.created_by, self._pprint_datetime(self.created_at))
        if self.updated_by is not None or self.updated_at is not None:
            update_str = '\nUpdated by user {} at time {}'.format(
                self.updated_by, self._pprint_datetime(self.updated_at))
        else:
            update_str = ''
        return create_str + update_str

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()

    @staticmethod
    def _pprint_datetime(create_time: int):
        return arrow.get(create_time / 1000).datetime

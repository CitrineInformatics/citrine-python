from uuid import UUID
from typing import Union


def normalize_uid(uid: Union[UUID, str]) -> UUID:
    if isinstance(uid, str):
        return UUID(uid)
    else:
        return uid

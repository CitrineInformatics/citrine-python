from uuid import UUID


def normalize_uid(uid: UUID | str) -> UUID:
    if isinstance(uid, str):
        return UUID(uid)
    else:
        return uid

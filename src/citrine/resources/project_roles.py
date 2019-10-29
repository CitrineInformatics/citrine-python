from typing import Union

LEAD = "LEAD"
MEMBER = "MEMBER"
ROLES = Union[LEAD, MEMBER]

WRITE = "WRITE"
READ = "READ"
ACTIONS = Union[WRITE, READ]

from typing import TypeVar, Optional, Union
from uuid import uuid4, UUID

from citrine._rest.collection import Collection
from citrine.exceptions import NotFound

ResourceType = TypeVar('ResourceType', bound='Resource')


def _norm(uid: Union[UUID, str]) -> UUID:
    if isinstance(uid, str):
        return UUID(uid)
    else:
        return uid


class FakeCollection(Collection[ResourceType]):

    def __init__(self):
        self._resources = {}

    def register(self, resource: ResourceType) -> ResourceType:
        if resource.uid is None:
            resource.uid = uuid4()
        self._resources[resource.uid] = resource
        return resource
    
    def update(self, resource):
        self._resources.pop(resource.uid, None)
        return self.register(resource)
    
    def list(self, page: Optional[int] = None, per_page: int = 100):
        if page is None:
            return iter(list(self._resources.values()))
        else:
            return iter(list(self._resources.values())[(page - 1)*per_page:page*per_page])
    
    def get(self, uid: Union[UUID, str]) -> ResourceType:
        if _norm(uid) not in self._resources:
            raise NotFound("")
        return self._resources[_norm(uid)]

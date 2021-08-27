from uuid import uuid4, UUID
from typing import TypeVar, Optional, Union, Iterable

from citrine._rest.collection import Collection
from citrine.exceptions import NotFound

from tests.utils.functions import normalize_uid

ResourceType = TypeVar('ResourceType', bound='Resource')


class FakeCollection(Collection[ResourceType]):

    def __init__(self):
        self._resources = {}

    def register(self, resource: ResourceType) -> ResourceType:
        if resource.uid is None:
            resource.uid = uuid4()
        self._resources[resource.uid] = resource
        return resource
    
    def update(self, resource: ResourceType):
        self._resources.pop(resource.uid, None)
        return self.register(resource)
    
    def list(self, page: Optional[int] = None, per_page: int = 100) -> Iterable[ResourceType]:
        if page is None:
            return iter(list(self._resources.values()))
        else:
            return iter(list(self._resources.values())[(page - 1)*per_page:page*per_page])
    
    def get(self, uid: Union[UUID, str]) -> ResourceType:
        if normalize_uid(uid) not in self._resources:
            raise NotFound("")
        return self._resources[normalize_uid(uid)]

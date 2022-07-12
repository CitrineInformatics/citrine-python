from abc import abstractmethod
from logging import getLogger
from typing import Optional, Union, Generic, TypeVar, Iterable, Iterator
from uuid import UUID

from citrine._rest.pageable import Pageable
from citrine._rest.paginator import Paginator
from citrine._rest.resource import ResourceRef
from citrine._utils.functions import format_escaped_url
from citrine.exceptions import ModuleRegistrationFailedException, NonRetryableException
from citrine.resources.response import Response

logger = getLogger(__name__)

ResourceType = TypeVar('ResourceType', bound='Resource')

# Python does not support a TypeVar being used as a bound for another TypeVar.
# Thus, this will never be particularly type safe on its own. The solution is to
# have subclasses override the create method.
CreationType = TypeVar('CreationType', bound='Resource')


class Collection(Generic[ResourceType], Pageable):
    """Abstract class for representing collections of REST resources."""

    _path_template: str = NotImplemented
    _dataset_agnostic_path_template: str = NotImplemented
    _individual_key: str = NotImplemented
    _resource: ResourceType = NotImplemented
    _collection_key: str = 'entries'
    _paginator: Paginator = Paginator()
    _api_version: str = "v1"

    def _put_resource_ref(self, subpath: str, uid: Union[UUID, str]):
        url = self._get_path(subpath)
        ref = ResourceRef(uid)
        return self.session.put_resource(url, ref.dump(), version=self._api_version)

    def _get_path(self, uid: Optional[Union[UUID, str]] = None,
                  ignore_dataset: Optional[bool] = False) -> str:
        """Construct a url from __base_path__ and, optionally, id."""
        subpath = format_escaped_url('/{}', uid) if uid else ''
        if ignore_dataset:
            return format_escaped_url(self._dataset_agnostic_path_template + subpath,
                                      **self.__dict__)
        else:
            return format_escaped_url(self._path_template + subpath,
                                      **self.__dict__)

    @abstractmethod
    def build(self, data: dict):
        """Build an individual element of the collection."""

    def get(self, uid: Union[UUID, str]) -> ResourceType:
        """Get a particular element of the collection."""
        if uid is None:
            raise ValueError("Cannot get when uid=None.  Are you using a registered resource?")
        path = self._get_path(uid)
        data = self.session.get_resource(path, version=self._api_version)
        data = data[self._individual_key] if self._individual_key else data
        return self.build(data)

    def register(self, model: CreationType) -> CreationType:
        """Create a new element of the collection by registering an existing resource."""
        path = self._get_path()
        try:
            data = self.session.post_resource(path, model.dump(), version=self._api_version)
            data = data[self._individual_key] if self._individual_key else data
            return self.build(data)
        except NonRetryableException as e:
            raise ModuleRegistrationFailedException(model.__class__.__name__, e)

    def list(self, *,
             page: Optional[int] = None,
             per_page: int = 100) -> Iterator[ResourceType]:
        """
        Paginate over the elements of the collection.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is to read all pages and yield
            all results.  This option is deprecated.
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        Returns
        -------
        Iterator[ResourceType]
            An iterator that can be used to loop over all of the resources in this collection.
            Use list() to force evaluation of all results into an in-memory list.

        """
        return self._paginator.paginate(page_fetcher=self._fetch_page,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
                                        per_page=per_page)

    def update(self, model: CreationType) -> CreationType:
        """Update a particular element of the collection."""
        url = self._get_path(model.uid)
        updated = self.session.put_resource(url, model.dump(), version=self._api_version)
        data = updated[self._individual_key] if self._individual_key else updated
        return self.build(data)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Delete a particular element of the collection."""
        url = self._get_path(uid)
        data = self.session.delete_resource(url, version=self._api_version)
        return Response(body=data)

    def _build_collection_elements(self,
                                   collection: Iterable[dict]) -> Iterator[ResourceType]:
        """
        For each element in the collection, build the appropriate resource type.

        Parameters
        ---------
        collection: Iterable[dict]
            collection containing the elements to be built

        Returns
        -------
        Iterator[ResourceType]
            Resources in this collection.

        """
        for element in collection:
            try:
                yield self.build(element)
            except(KeyError, ValueError) as e:
                # TODO(PLA-9109): This is a patch to handle deprecated predictors client side
                # Remove when predictors are migrated
                logger.warning(f"Building element skipped due to error: {e}")
                pass

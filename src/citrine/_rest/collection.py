from abc import abstractmethod
from typing import Optional, Union, Generic, TypeVar, Iterable, Iterator, Sequence, Dict
from uuid import UUID

from citrine._rest.pageable import Pageable
from citrine._rest.paginator import Paginator
from citrine._rest.resource import Resource, ResourceRef
from citrine._utils.functions import resource_path
from citrine.exceptions import ModuleRegistrationFailedException, NonRetryableException
from citrine.resources.response import Response

ResourceType = TypeVar('ResourceType', bound=Resource)

# Python does not support a TypeVar being used as a bound for another TypeVar.
# Thus, this will never be particularly type safe on its own. The solution is to
# have subclasses override the create method.
CreationType = TypeVar('CreationType', bound='Resource')


class Collection(Generic[ResourceType], Pageable):
    """Base class for server-backed resource collections.

    A Collection provides CRUD operations for a specific
    resource type. All collections support at minimum:

    * ``get(uid)`` — fetch one resource by UID
    * ``list()`` — paginate over all resources
    * ``register(model)`` — create a new resource
    * ``update(model)`` — update an existing resource
    * ``delete(uid)`` — delete a resource

    Concrete collections (e.g. ``ProjectCollection``,
    ``DatasetCollection``) may add additional operations.

    """

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

    def _get_path(self,
                  uid: Optional[Union[UUID, str]] = None,
                  *,
                  ignore_dataset: bool = False,
                  action: Union[str, Sequence[str]] = [],
                  query_terms: Dict[str, str] = {},
                  ) -> str:
        """Construct a url from __base_path__ and, optionally, id and/or action."""
        base = self._dataset_agnostic_path_template if ignore_dataset else self._path_template
        return resource_path(path_template=base, uid=uid, action=action, query_terms=query_terms,
                             **self.__dict__)

    @abstractmethod
    def build(self, data: dict):
        """Build an individual element of the collection."""

    def get(self, uid: Union[UUID, str]) -> ResourceType:
        """Fetch a single resource by its unique identifier.

        Parameters
        ----------
        uid : UUID or str
            The unique identifier of the resource.

        Returns
        -------
        ResourceType
            The resource object.

        Raises
        ------
        ValueError
            If ``uid`` is None (the object may not be
            registered yet).
        NotFound
            If no resource with the given UID exists.

        """
        if uid is None:
            raise ValueError("Cannot get when uid=None.  Are you using a registered resource?")
        path = self._get_path(uid)
        data = self.session.get_resource(path, version=self._api_version)
        data = data[self._individual_key] if self._individual_key else data
        return self.build(data)

    def register(self, model: CreationType) -> CreationType:
        """Create a new resource on the platform.

        Parameters
        ----------
        model : ResourceType
            The resource to register. After registration, the
            returned object will have a platform-assigned UID.

        Returns
        -------
        ResourceType
            The registered resource with server-assigned fields.

        Raises
        ------
        ModuleRegistrationFailedException
            If the platform rejects the resource.

        """
        path = self._get_path()
        try:
            data = self.session.post_resource(path, model.dump(), version=self._api_version)
            data = data[self._individual_key] if self._individual_key else data
            return self.build(data)
        except NonRetryableException as e:
            raise ModuleRegistrationFailedException(model.__class__.__name__, e)

    def list(self, *, per_page: int = 100) -> Iterator[ResourceType]:
        """
        Paginate over the elements of the collection.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        Returns
        -------
        Iterator[ResourceType]
            An iterator that can be used to loop over all the resources in this collection.
            Use list() to force evaluation of all results into an in-memory list.

        """
        return self._paginator.paginate(page_fetcher=self._fetch_page,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def update(self, model: CreationType) -> CreationType:
        """Update an existing resource on the platform.

        Parameters
        ----------
        model : ResourceType
            The resource with updated fields. Must have a
            valid ``uid`` (i.e., be previously registered).

        Returns
        -------
        ResourceType
            The updated resource as returned by the server.

        """
        url = self._get_path(model.uid)
        updated = self.session.put_resource(url, model.dump(), version=self._api_version)
        data = updated[self._individual_key] if self._individual_key else updated
        return self.build(data)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Delete a resource by its unique identifier.

        Parameters
        ----------
        uid : UUID or str
            The unique identifier of the resource to delete.

        Returns
        -------
        Response
            The server response.

        """
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
            yield self.build(element)

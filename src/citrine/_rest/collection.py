import warnings
from abc import abstractmethod
from typing import Optional, Union, Generic, TypeVar, Iterable, Dict, Tuple, Callable
from uuid import UUID

from citrine._rest.paginator import Paginator
from citrine.exceptions import ModuleRegistrationFailedException, NonRetryableException
from citrine.resources.response import Response

ResourceType = TypeVar('ResourceType', bound='Resource')

# Python does not support a TypeVar being used as a bound for another TypeVar.
# Thus, this will never be particularly type safe on its own. The solution is to
# have subclasses override the create method.
CreationType = TypeVar('CreationType', bound='Resource')


class Collection(Generic[ResourceType]):
    """Abstract class for representing collections of REST resources."""

    _path_template: str = NotImplemented
    _dataset_agnostic_path_template: str = NotImplemented
    _individual_key: str = NotImplemented
    _resource: ResourceType = NotImplemented
    _collection_key: str = 'entries'
    _paginator: Paginator = Paginator()

    def _get_path(self, uid: Optional[Union[UUID, str]] = None,
                  ignore_dataset: Optional[bool] = False) -> str:
        """Construct a url from __base_path__ and, optionally, id."""
        subpath = '/{}'.format(uid) if uid else ''
        if ignore_dataset:
            return self._dataset_agnostic_path_template.format(**self.__dict__) + subpath
        else:
            return self._path_template.format(**self.__dict__) + subpath

    @abstractmethod
    def build(self, data: dict):
        """Build an individual element of the collection."""

    def get(self, uid: Union[UUID, str]) -> ResourceType:
        """Get a particular element of the collection."""
        path = self._get_path(uid)
        data = self.session.get_resource(path)
        data = data[self._individual_key] if self._individual_key else data
        return self.build(data)

    def register(self, model: CreationType) -> CreationType:
        """Create a new element of the collection by registering an existing resource."""
        path = self._get_path()
        try:
            data = self.session.post_resource(path, model.dump())
            data = data[self._individual_key] if self._individual_key else data
            self._check_experimental(data)
            return self.build(data)
        except NonRetryableException as e:
            raise ModuleRegistrationFailedException(model.__class__.__name__, e)

    def list(self,
             page: Optional[int] = None,
             per_page: int = 100) -> Iterable[ResourceType]:
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
        Iterable[ResourceType]
            Resources in this collection.

        """
        return self._paginator.paginate(page_fetcher=self._fetch_page,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
                                        per_page=per_page)

    def update(self, model: CreationType) -> CreationType:
        """Update a particular element of the collection."""
        url = self._get_path(model.uid)
        updated = self.session.put_resource(url, model.dump())
        data = updated[self._individual_key] if self._individual_key else updated
        self._check_experimental(data)
        return self.build(data)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Delete a particular element of the collection."""
        url = self._get_path(uid)
        data = self.session.delete_resource(url)
        return Response(body=data)

    def _fetch_page(self,
                    path: Optional[str] = None,
                    fetch_func: Optional[Callable[..., dict]] = None,
                    page: Optional[int] = None,
                    per_page: Optional[int] = None,
                    json_body: Optional[dict] = None) -> Tuple[Iterable[dict], str]:
        """
        Fetch visible elements in the collection.  This does not handle pagination.

        Method can be used with any function that fetches a list of resources.

        This method will return the first page of results using the default page/per_page behavior
        of the backend service.  Specify page/per_page to override these defaults which are passed
        to the backend service.

        Parameters
        ---------
        path: str, optional
            The path for the endpoint that will be called to fetch the resources. Will default to
            root path
        fetch_func: Callable[..., dict], optional
            The function that will make the official request that returns the list of resources ie.
            (checked_post, etc.). Will default to get_resource
        page: int, optional
            The "page" of results to list. Default is the first page, which is 1.
        per_page: int, optional
            Max number of results to return. Default is 20.
        json_body: dict, optional
            A dict representing a request body that could be sent to a POST request. The "json"
            field should be passed as the key for the outermost dict, with its value the request
            body, so that we can easily unpack the keyword argument when it gets passed to
            fetch_func.
            ie.
            {'json':
                {'search_params': {'name': {'value': 'Project', 'search_method': 'SUBSTRING'}}}
            }

        Returns
        -------
        Iterable[dict]
            Elements in this collection.
        str
            The next uri if one is available, empty string otherwise

        """
        # To avoid setting defaults -> reduce mutation risk, and to make more extensible
        path = self._get_path() if path is None else path
        fetch_func = self.session.get_resource if fetch_func is None else fetch_func
        json_body = {} if json_body is None else json_body

        module_type = getattr(self, '_module_type', None)
        params = self._page_params(page, per_page, module_type)

        data = fetch_func(path, params=params, **json_body)

        try:
            next_uri = data.get('next', "")
        except AttributeError:
            next_uri = ""

        # A 'None' collection key implies response has a top-level array
        # of 'ResourceType'
        # TODO: Unify backend return values
        if self._collection_key is None:
            collection = data
        else:
            collection = data[self._collection_key]

        return collection, next_uri

    def _build_collection_elements(self,
                                   collection: Iterable[dict]) -> Iterable[ResourceType]:
        """
        For each element in the collection, build the appropriate resource type.

        Parameters
        ---------
        collection: Iterable[dict]
            collection containing the elements to be built

        Returns
        -------
        Iterable[ResourceType]
            Resources in this collection.

        """
        for element in collection:
            try:
                yield self.build(element)
            except(KeyError, ValueError):
                # TODO:  Right now this is a hack.  Clean this up soon.
                # Module collections are not filtering on module type
                # properly, so we are filtering client-side.
                pass

    def _page_params(self,
                     page: Optional[int],
                     per_page: Optional[int],
                     module_type: Optional[str] = None) -> Dict[str, int]:
        params = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if module_type is not None:
            params["module_type"] = module_type
        return params

    def _check_experimental(self, data):
        if data.get("experimental", False):
            uid = data.get("id")
            typ = self._resource().__class__.__name__
            msg = "The {} with id {} is experimental because: \n  {}".format(
                typ, uid,
                "\n  ".join(data.get("experimental_reasons") or ["Unknown reason"])
            )
            warnings.warn(msg)

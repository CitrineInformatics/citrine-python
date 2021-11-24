from logging import getLogger
from typing import Optional, Iterable, Dict, Tuple, Callable, Union
from uuid import UUID


logger = getLogger(__name__)


class Pageable():
    """Class that allows paging."""

    _collection_key: str = NotImplemented
    _api_version: str = "v1"

    def _get_path(self, uid: Optional[Union[UUID, str]] = None,
                  ignore_dataset: Optional[bool] = False) -> str:
        """Construct a url from __base_path__ and, optionally, id."""
        raise NotImplementedError  # pragma: no cover

    def _fetch_page(self,
                    path: Optional[str] = None,
                    fetch_func: Optional[Callable[..., dict]] = None,
                    page: Optional[int] = None,
                    per_page: Optional[int] = None,
                    json_body: Optional[dict] = None,
                    additional_params: Optional[dict] = None,
                    ) -> Tuple[Iterable[dict], str]:
        """
        Fetch visible elements.  This does not handle pagination.

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
        additional_params: dict, optional
            A dict that allows extra parameters to be added to the request parameters

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
        params.update(additional_params or {})

        data = fetch_func(path, params=params, version=self._api_version, **json_body)

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

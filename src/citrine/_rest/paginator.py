import warnings
from typing import TypeVar, Generic, Callable, Optional, Iterable, Any, Tuple
from uuid import uuid4

ResourceType = TypeVar('ResourceType')


class Paginator(Generic[ResourceType]):
    """
    This generically pages over a resource, given a page_fetcher callable.

    One can override this class to fine-tune the components of the objects
    that will be extracted for comparison purposes (to avoid looping on the same items).
    """

    def paginate(self,
                 page_fetcher: Callable[[Optional[int], int], Tuple[Iterable[dict], str]],
                 collection_builder: Callable[[Iterable[dict]], Iterable[ResourceType]],
                 page: Optional[int] = None,
                 per_page: int = 100,
                 search_params: Optional[dict] = None,
                 deduplicate: bool = True) -> Iterable[ResourceType]:
        """
        A generic support class to paginate requests into an iterable of a built object.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        The page fetcher returns an Iterable of subsequent items on every invocation,
        returning an empty iterable when fetching is finished.

        Parameters
        ---------
        page_fetcher: Callable[[Optional[int], int], Tuple[Iterable[dict], str]]
            Fetches the next page of elements
        collection_builder: Callable[[Iterable[dict]], Iterable[ResourceType]]
            Builds each element in the collection into the appropriate resource
        page: int, optional
            The "page" of results to list. Default is to read all pages and yield
            all results.  This option is deprecated.
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.
        search_params: dict, Optional
            A dictionary representing the request body to a page_fetcher function. The
            page_fetcher function should have a key word argument "search_params" should it
            pass a request body to the target endpoint. If no search_params are supplied,
            no search_params argument will get passed to the page_fetcher function.
        deduplicate: bool, optional
            Whether or not to deduplicate the yielded resources by their uid.  The default
            is true.

        Returns
        -------
        Iterable[ResourceType]
            Resources in this collection.

        """
        # To avoid setting default to {} -> reduce mutation risk, and to make more extensible. Also
        # making 'search_params' key of outermost dict for keyword expansion by page_fetcher func
        search_params = {} if search_params is None else {'search_params': search_params}

        if page is not None:
            warnings.warn("The page parameter is deprecated, default is automatic pagination",
                          DeprecationWarning)

        first_entity = None
        page_idx = page
        uids = set()

        while True:
            subset_collection, next_uri = page_fetcher(page=page_idx, per_page=per_page,
                                                       **search_params)

            subset = collection_builder(subset_collection)

            count = 0
            for idx, element in enumerate(subset):

                # escaping from infinite loops where page/per_page are not
                # honored and are returning the same results regardless of page:
                current_entity = self._comparison_fields(element)
                if first_entity is not None and \
                        first_entity == current_entity:
                    # TODO: raise an exception once the APIs that ignore pagination are fixed
                    break

                # Only return new uids.  This way, if an element shows up at the end of one page
                # and then at the beginning of the next one because a new resource in the same
                # collection was created, it is only returned from the list method once.  uids are
                # unique, so this should be safe.  If a user is listing enough elements that the
                # size of uids is too big, there will be other problems first. This could be
                # replaced by a deque with a fixed size if memory is really an issue, at the cost
                # of slower lookups.  Or something more complex for both :-)
                # If no uid is available, create one, which will never deduplicate
                uid = getattr(element, "uid", uuid4())
                if not deduplicate or uid not in uids:
                    uids.add(uid)
                    yield element

                if first_entity is None:
                    first_entity = current_entity

                count += 1

            # If the page number is specified we exit to disable auto-paginating
            if page is not None:
                break

            # Handle the case where we get an unexpected number of results (e.g. last page)
            if next_uri == "" and count < per_page:
                break

            if page_idx is None:
                page_idx = 2
            else:
                page_idx += 1

    def _comparison_fields(self, entity: ResourceType) -> Any:
        """
        Extract the uniquely identifying attributes for equality comparison.

        If the 'uid' here isn't found, default to comparing the entire entity.
        """
        return getattr(entity, 'uid', entity)

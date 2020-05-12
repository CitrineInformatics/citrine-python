import warnings
from typing import TypeVar, Generic, Callable, Optional, Iterable, Any, Tuple

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
                 per_page: int = 100) -> Iterable[ResourceType]:
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

        Returns
        -------
        Iterable[ResourceType]
            Resources in this collection.

        """
        if page is not None:
            warnings.warn("The page parameter is deprecated, default is automatic pagination",
                          DeprecationWarning)

        first_entity = None
        page_idx = page

        while True:
            subset_collection, next_uri = page_fetcher(page_idx, per_page)
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

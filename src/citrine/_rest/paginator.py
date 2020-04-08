import warnings
from typing import TypeVar, Generic, Callable, Optional, Iterable, Dict, Any

ResourceType = TypeVar('ResourceType')


class Paginator(Generic[ResourceType]):

    def paginate(self,
                 page_fetcher: Callable[[Optional[int], int], Iterable[ResourceType]],
                 page: Optional[int] = None,
                 per_page: int = 100) -> Iterable[ResourceType]:
        """
        Paginate generically over the items returned by the page fetcher, parameterized
        by the callable passed in. This allows us to paginate over different data suppliers.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        The page fetcher returns an Iterable of subsequent items on every invocation,
        returning an empty iterable when fetching is finished.

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

        if page is not None:
            warnings.warn("The page parameter is deprecated, default is automatic pagination",
                          DeprecationWarning)

        first_unique_identifiers = None
        page_idx = page

        while True:
            subset = page_fetcher(page_idx, per_page)

            count = 0
            for idx, element in enumerate(subset):

                # escaping from infinite loops where page/per_page are not
                # honored and are returning the same results regardless of page:
                unique_identifiers = self._extract_unique_identifiers(element)
                if first_unique_identifiers is not None and first_unique_identifiers == unique_identifiers:
                    # TODO: raise an exception once the APIs that ignore pagination are fixed
                    break

                yield element

                if first_unique_identifiers is None:
                    first_unique_identifiers = unique_identifiers

                count += 1

            # If the page number is specified we exit to disable auto-paginating
            if page is not None:
                break

            # Handle the case where we get an unexpected number of results (e.g. last page)
            if count == 0 or count < per_page:
                break

            if page_idx is None:
                page_idx = 2
            else:
                page_idx += 1

    def _extract_unique_identifiers(self, entity: ResourceType) -> Any:
        """
        Extract the uniquely identifying attributes from the resource type into an object we can
        compare for equality.

        If the 'uid' here isn't found, default to comparing the entire entity.
        """
        return getattr(entity, 'uid', entity)
